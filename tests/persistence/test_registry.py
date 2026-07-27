"""Tests for infra.persistence.registry — Phase 15.0 T2"""
import sqlite3
from pathlib import Path
from threading import Thread
from time import sleep

import pytest

from infra.persistence.bootstrap import register_all
from infra.persistence.registry import (
    get,
    get_registration,
    is_registered,
    list_registered,
    register,
    reset,
    reset_all,
)


class MockStorage:
    def __init__(self, db_path=None, **kwargs):
        self.db_path = db_path
        self.kwargs = kwargs


class TestRegistryBasics:
    def setup_method(self):
        reset_all()

    def teardown_method(self):
        reset_all()

    def test_register_and_get(self):
        register("test", MockStorage, Path(":memory:"))
        storage = get("test")
        assert isinstance(storage, MockStorage)
        assert str(storage.db_path) == ":memory:"

    def test_get_non_existent(self):
        with pytest.raises(KeyError, match="No storage registered with name"):
            get("non_existent")

    def test_is_registered(self):
        assert not is_registered("test_is_registered_unique")
        register("test_is_registered_unique", MockStorage, Path(":memory:"))
        assert is_registered("test_is_registered_unique")

    def test_list_registered(self):
        register("test1", MockStorage, Path(":memory:"))
        register("test2", MockStorage, Path(":memory:"))
        registered = list_registered()
        assert "test1" in registered
        assert "test2" in registered

    def test_reset(self):
        register("test", MockStorage, Path(":memory:"))
        first_instance = get("test")
        reset("test")
        second_instance = get("test")
        assert first_instance is not second_instance

    def test_reset_all(self):
        register("test1", MockStorage, Path(":memory:"))
        register("test2", MockStorage, Path(":memory:"))
        first1 = get("test1")
        first2 = get("test2")
        reset_all()
        second1 = get("test1")
        second2 = get("test2")
        assert first1 is not second1
        assert first2 is not second2

    def test_get_registration(self):
        register("test", MockStorage, Path(":memory:"))
        reg = get_registration("test")
        assert reg is not None
        assert reg.name == "test"
        assert reg.cls == MockStorage
        assert str(reg.db_path) == ":memory:"

    def test_get_with_custom_db_path(self):
        register("test", MockStorage, Path(":memory:"))
        storage = get("test", db_path=":memory:")
        assert isinstance(storage, MockStorage)


class TestRegistrySingleton:
    def setup_method(self):
        reset_all()

    def teardown_method(self):
        reset_all()

    def test_singleton_return(self):
        register("test", MockStorage, Path(":memory:"))
        first = get("test")
        second = get("test")
        assert first is second

    def test_custom_path_creates_new_instance(self):
        register("test", MockStorage, Path("/tmp/test1.db"))
        first = get("test")
        second = get("test", db_path="/tmp/test2.db")
        assert first is not second


class TestRegistryThreadSafety:
    def setup_method(self):
        reset_all()

    def teardown_method(self):
        reset_all()

    def test_concurrent_get(self):
        register("test", MockStorage, Path(":memory:"))
        instances = []

        def get_instance():
            instances.append(get("test"))
            sleep(0.01)

        threads = [Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(instances) == 10
        first = instances[0]
        for inst in instances[1:]:
            assert inst is first


class TestRegistryIntegration:
    def setup_method(self):
        reset_all()

    def teardown_method(self):
        reset_all()

    def test_register_all(self):
        register_all()
        registered = list_registered()
        assert "ripple" in registered
        assert "cost" in registered
        assert "budget" in registered
        assert "workflow" in registered
        assert "reading" in registered
        assert "relationship" in registered

    def test_get_ripple_storage(self):
        register_all()
        storage = get("ripple")
        from infra.cross_volume.storage import RippleStorage

        assert isinstance(storage, RippleStorage)

    def test_get_cost_storage(self):
        register_all()
        storage = get("cost")
        from infra.agent_system.cost_persistence import CostTrackerDB

        assert isinstance(storage, CostTrackerDB)
