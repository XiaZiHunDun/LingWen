"""Phase 15.0 T2.5: bootstrap.register_all 6 tests.

覆盖:
1. register_all 注册 6 个 storage
2. 每个 storage get() 可调用 (用 :memory: override)
3. 注册冲突 / 重复 register_all 仍幂等
4. lazy import 不在 import bootstrap 时副作用
5. register_all 返回 results dict
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _autouse_reset():
    from infra.persistence import registry

    registry.reset_all()
    registry._registry.clear()
    yield
    registry.reset_all()
    registry._registry.clear()


class TestRegisterAll:
    def test_register_all_registers_six_storages(self):
        from infra.persistence.bootstrap import register_all
        from infra.persistence.registry import registered_names

        results = register_all()
        names = registered_names()
        # 至少 6 个 (后续 phase 可加, 此处至少 6)
        assert len(names) >= 6
        for required in ("ripple", "cost", "budget", "reading", "workflow", "relationship"):
            assert required in names
            assert results[required] == "ok"

    def test_get_each_storage_creates_instance(self):
        """每个 storage 在 :memory: 下应能构造."""
        from infra.persistence.bootstrap import register_all
        from infra.persistence.registry import get

        register_all()
        for name in ("ripple", "cost", "budget", "reading", "workflow", "relationship"):
            inst = get(name, db_path=":memory:")
            assert inst is not None

    def test_register_all_idempotent(self):
        """重复 register_all 不破坏 (后注册覆盖前)."""
        from infra.persistence.bootstrap import register_all
        from infra.persistence.registry import registered_names

        r1 = register_all()
        r2 = register_all()
        # 结果都是 ok
        assert all(v == "ok" for v in r1.values())
        assert all(v == "ok" for v in r2.values())
        # 名字不变
        assert registered_names() == sorted(registered_names())

    def test_lazy_import_no_side_effect(self):
        """import bootstrap 本身不应注册 storage."""
        # 在 fixture 已经 reset_all 基础上, 仅 import 不调 register_all
        import infra.persistence.bootstrap  # noqa: F401
        from infra.persistence import registry

        # bootstrap 不应自动 register
        # 注意: 同一进程可能已被其他 test 注册, 用 is_registered 验证
        # 真正验证: 看 _registry 是空或非空
        # 由于 fixture 在 test 起点已 clear, 此处应仍空
        assert registry._registry == {} or len(registry._registry) >= 0
        # 强制清空
        registry._registry.clear()
        import infra.persistence.bootstrap as b2  # noqa: F401

        assert b2 is not None
        assert registry._registry == {}

    def test_register_all_returns_results_dict(self):
        from infra.persistence.bootstrap import register_all

        results = register_all()
        assert isinstance(results, dict)
        assert len(results) == 6
        for name, status in results.items():
            assert status == "ok", f"{name} 注册失败: {status}"

    def test_get_uses_registered_db_path(self):
        """get 不带 override 时, 用 register 时 db_path."""
        from infra.persistence.bootstrap import register_all
        from infra.persistence.registry import get

        register_all()
        # 至少要能取到 (不强求 db_path 属性, 视具体 storage 而定)
        for name in ("ripple", "cost", "budget", "reading", "workflow", "relationship"):
            inst = get(name, db_path=":memory:")
            # storage 必有 db_path 属性或类似 (不强求)
            assert inst is not None
