"""Phase 15.0 T2.1: registry.py 14 tests.

覆盖:
1. register + get singleton
2. lazy instantiate
3. reset
4. reset_all
5. db_path override
6. unknown name KeyError
7. 防御 non-callable cls
8. thread safety
9. db_path argument priority
10. reset unknown noop
11. 重名 register
12. kwargs passthrough
13. registry 独立
14. test isolation (autouse conftest)
"""
from __future__ import annotations

import threading

import pytest


class _FakeStorage:
    """最小 storage 替身: 接收 db_path, 记录构造次数."""

    instance_count = 0

    def __init__(self, db_path=None, extra=None, **kwargs):
        _FakeStorage.instance_count += 1
        self.db_path = db_path
        self.extra = extra
        self.kwargs = kwargs


@pytest.fixture(autouse=True)
def _autouse_reset():
    """每个 test 前清空 registry + instances + 重置 fake counter."""
    from infra.persistence import registry

    registry.reset_all()
    registry._registry.clear()
    _FakeStorage.instance_count = 0
    yield
    registry.reset_all()
    registry._registry.clear()


class TestRegisterAndGet:
    def test_register_and_get_singleton(self):
        from infra.persistence.registry import get, register

        register("fake", _FakeStorage, db_path="/tmp/a.db")
        a = get("fake")
        b = get("fake")
        assert a is b
        assert _FakeStorage.instance_count == 1

    def test_get_lazily_instantiates(self):
        from infra.persistence.registry import get, register

        register("lazy", _FakeStorage, db_path="/tmp/lazy.db")
        assert _FakeStorage.instance_count == 0
        a = get("lazy")
        assert _FakeStorage.instance_count == 1
        b = get("lazy")
        assert _FakeStorage.instance_count == 1
        assert a is b

    def test_reset_clears_singleton(self):
        from infra.persistence.registry import get, register, reset

        register("r", _FakeStorage, db_path="/tmp/r.db")
        a = get("r")
        reset("r")
        b = get("r")
        assert a is not b
        assert _FakeStorage.instance_count == 2

    def test_reset_all_clears_everything(self):
        from infra.persistence.registry import get, register, reset_all

        register("a", _FakeStorage, db_path="/tmp/a.db")
        register("b", _FakeStorage, db_path="/tmp/b.db")
        a1 = get("a")
        b1 = get("b")
        reset_all()
        a2 = get("a")
        b2 = get("b")
        assert a1 is not a2
        assert b1 is not b2
        assert _FakeStorage.instance_count == 4

    def test_register_with_db_path_override(self):
        from infra.persistence.registry import get, register

        register("ovr", _FakeStorage, db_path="/tmp/default.db")
        inst = get("ovr", db_path=":memory:")
        assert inst.db_path == ":memory:"

    def test_unknown_name_raises(self):
        from infra.persistence.registry import get

        with pytest.raises(KeyError) as exc_info:
            get("nope")
        assert "nope" in str(exc_info.value)
        assert "未注册" in str(exc_info.value)

    def test_register_non_callable_raises(self):
        from infra.persistence.registry import register

        with pytest.raises(TypeError) as exc_info:
            register("bad", 12345)
        assert "可调用" in str(exc_info.value)

    def test_thread_safety_concurrent_get(self):
        from infra.persistence.registry import get, register

        register("thread", _FakeStorage, db_path="/tmp/thread.db")
        results = []
        barrier = threading.Barrier(20)

        def worker():
            barrier.wait()
            results.append(get("thread"))

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert all(r is results[0] for r in results)
        assert _FakeStorage.instance_count == 1

    def test_db_path_argument_priority(self):
        from infra.persistence.registry import get, register

        register("prio", _FakeStorage, db_path="/tmp/registered.db")
        inst_default = get("prio")
        inst_override = get("prio", db_path="/tmp/override.db")
        assert inst_default.db_path == "/tmp/registered.db"
        assert inst_override.db_path == "/tmp/override.db"

    def test_reset_unknown_name_noop(self):
        from infra.persistence.registry import reset

        reset("does-not-exist")
        assert True  # 不抛即通过

    def test_register_then_reset_then_register(self):
        from infra.persistence.registry import get, register, reset

        register("rebind", _FakeStorage, db_path="/tmp/v1.db")
        a = get("rebind")
        reset("rebind")
        register("rebind", _FakeStorage, db_path="/tmp/v2.db")
        b = get("rebind")
        assert a is not b
        assert b.db_path == "/tmp/v2.db"

    def test_get_with_kwargs_passthrough(self):
        from infra.persistence.registry import get, register

        register("kw", _FakeStorage, db_path="/tmp/kw.db", extra="from_register")
        inst = get("kw", extra="from_get")
        # get 时 kwargs 应覆盖 register 时
        assert inst.extra == "from_get"

    def test_registry_independent_per_name(self):
        from infra.persistence.registry import get, register, reset

        register("one", _FakeStorage, db_path="/tmp/one.db")
        register("two", _FakeStorage, db_path="/tmp/two.db")
        a1 = get("one")
        b1 = get("two")
        reset("one")
        a2 = get("one")
        b2 = get("two")
        assert a1 is not a2
        assert b1 is b2  # two 未 reset, 应保持

    def test_isolation_between_tests(self):
        """autouse reset_all 保证 test 间不污染."""
        from infra.persistence.registry import (
            get,
            is_registered,
            register,
            registered_names,
        )

        register("iso1", _FakeStorage, db_path="/tmp/iso1.db")
        register("iso2", _FakeStorage, db_path="/tmp/iso2.db")
        assert "iso1" in registered_names()
        assert "iso2" in registered_names()
        assert is_registered("iso1")
        # fixture 清理后 (下个 test 起点): 全空
        # 此 test 自身结束时 fixture 会 cleanup

    def test_get_raises_includes_registered_list(self):
        from infra.persistence.registry import get, register

        register("alpha", _FakeStorage, db_path="/tmp/alpha.db")
        register("beta", _FakeStorage, db_path="/tmp/beta.db")
        with pytest.raises(KeyError) as exc_info:
            get("gamma")
        msg = str(exc_info.value)
        assert "alpha" in msg
        assert "beta" in msg
