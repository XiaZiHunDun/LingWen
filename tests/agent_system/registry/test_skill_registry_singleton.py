"""
R2-017: SkillRegistry 单例并发安全测试

之前 get_registry() 用 `if _x is None: _x = X()` 模式 —
多线程同时进入 None 分支会重复创建实例,浪费 IO(YAML 加载) +
可能让 _variant_configs 缓存分裂。
reset_registry() 也没加锁,与正在 init 的线程 race。

修复:双重检查锁 (Double-Checked Locking) 模式。
"""
import threading
from unittest import TestCase

from infra.agent_system.registry.skill_registry import (
    SkillRegistry,
    get_registry,
    reset_registry,
)


class TestSkillRegistrySingleton(TestCase):
    """R2-017: 单例语义保留 + 多线程下不重复创建"""

    def setUp(self):
        reset_registry()

    def tearDown(self):
        reset_registry()

    def test_get_registry_returns_singleton(self):
        """单线程下 get_registry() 多次返回同一实例"""
        a = get_registry()
        b = get_registry()
        self.assertIs(a, b)

    def test_reset_creates_new_instance(self):
        """reset 后再次 get_registry() 返回新实例"""
        a = get_registry()
        reset_registry()
        b = get_registry()
        self.assertIsNot(a, b)

    def test_concurrent_get_registry_returns_single_instance(self):
        """多线程同时 get_registry() 只应创建一个实例

        修复前:可能创建 N 个 (N = thread count),每个都重新 load YAML。
        修复后:锁 + 双重检查,保证单例。
        """
        instances = []
        barrier = threading.Barrier(8)

        def worker():
            barrier.wait()  # 同步起跑,放大 race 窗口
            instances.append(get_registry())

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 所有线程拿到的应是同一实例
        first = instances[0]
        for inst in instances[1:]:
            self.assertIs(inst, first)

    def test_concurrent_reset_and_get_no_crash(self):
        """并发 reset + get_registry() 不应抛异常或返回损坏状态"""
        errors = []

        def reset_worker():
            try:
                for _ in range(20):
                    reset_registry()
            except Exception as e:
                errors.append(e)

        def get_worker():
            try:
                for _ in range(20):
                    r = get_registry()
                    # 拿到的一定是 SkillRegistry 实例
                    self.assertIsInstance(r, SkillRegistry)
            except Exception as e:
                errors.append(e)

        t_reset = threading.Thread(target=reset_worker)
        t_get1 = threading.Thread(target=get_worker)
        t_get2 = threading.Thread(target=get_worker)
        t_reset.start()
        t_get1.start()
        t_get2.start()
        t_reset.join()
        t_get1.join()
        t_get2.join()

        self.assertEqual(errors, [], f"并发 race 触发异常: {errors}")

    def test_reset_idempotent(self):
        """reset 在没有单例时也可调用(无锁版会触发 NameError/竞态)"""
        # 两次连续 reset,均不应抛
        reset_registry()
        reset_registry()
        # 之后 get_registry 仍能正常工作
        r = get_registry()
        self.assertIsInstance(r, SkillRegistry)
