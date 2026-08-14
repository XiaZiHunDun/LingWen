"""Phase 18.0 守卫测试 — lingwen_core.ports 包结构与类型契约。

Ports 是包对外接口的 Protocol 定义。所有 use-case / studio_api
应通过这些 Port 与底层实现（LLM、storage、checker）解耦。
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


def test_ports_package_importable():
    """ports/ 目录可作为 Python 包导入。"""
    import lingwen_core.ports  # noqa: F401


def test_storage_port_importable():
    from lingwen_core.ports.storage import StoragePort, EventStorePort  # noqa: F401


def test_llm_port_importable():
    from lingwen_core.ports.llm import LLMPort, EmbeddingPort  # noqa: F401


def test_checker_port_importable():
    from lingwen_core.ports.checker import CheckerPort  # noqa: F401


def test_storage_port_is_protocol():
    """StoragePort 必须是 runtime_checkable Protocol（用于依赖注入 duck typing）。"""
    from lingwen_core.ports.storage import StoragePort

    assert isinstance(StoragePort, runtime_checkable(Protocol)) or hasattr(
        StoragePort, "_is_protocol"
    )


def test_event_store_port_is_protocol():
    from lingwen_core.ports.storage import EventStorePort

    assert isinstance(EventStorePort, runtime_checkable(Protocol)) or hasattr(
        EventStorePort, "_is_protocol"
    )


def test_llm_port_is_protocol():
    from lingwen_core.ports.llm import LLMPort

    assert isinstance(LLMPort, runtime_checkable(Protocol)) or hasattr(
        LLMPort, "_is_protocol"
    )


def test_embedding_port_is_protocol():
    from lingwen_core.ports.llm import EmbeddingPort

    assert isinstance(EmbeddingPort, runtime_checkable(Protocol)) or hasattr(
        EmbeddingPort, "_is_protocol"
    )


def test_checker_port_is_protocol():
    from lingwen_core.ports.checker import CheckerPort

    assert isinstance(CheckerPort, runtime_checkable(Protocol)) or hasattr(
        CheckerPort, "_is_protocol"
    )


def _port_required_attrs(port_cls) -> list[str]:
    """提取 Protocol 类声明的所有方法名。

    Protocol 方法存在 __protocol_attrs__ 中（Python 3.12+）。
    """
    return list(getattr(port_cls, "__protocol_attrs__", ()))


def test_storage_port_methods():
    """StoragePort 必须声明 save / load / delete 方法。"""
    from lingwen_core.ports.storage import StoragePort

    attrs = set(_port_required_attrs(StoragePort))
    assert {"save", "load", "delete"} <= attrs


def test_event_store_port_methods():
    """EventStorePort 必须声明 append / replay 方法（事件溯源）。"""
    from lingwen_core.ports.storage import EventStorePort

    attrs = set(_port_required_attrs(EventStorePort))
    assert {"append", "replay"} <= attrs


def test_llm_port_methods():
    """LLMPort 必须声明 complete 方法（同步）。"""
    from lingwen_core.ports.llm import LLMPort

    attrs = set(_port_required_attrs(LLMPort))
    assert "complete" in attrs


def test_embedding_port_methods():
    """EmbeddingPort 必须声明 embed 方法。"""
    from lingwen_core.ports.llm import EmbeddingPort

    attrs = set(_port_required_attrs(EmbeddingPort))
    assert "embed" in attrs


def test_checker_port_methods():
    """CheckerPort 必须声明 check 方法。"""
    from lingwen_core.ports.checker import CheckerPort

    attrs = set(_port_required_attrs(CheckerPort))
    assert "check" in attrs


def test_mock_storage_port_satisfies_protocol():
    """InMemoryStoragePort 必须满足 StoragePort（runtime_checkable duck typing）。"""
    from lingwen_core.ports.storage import StoragePort, InMemoryStoragePort

    store = InMemoryStoragePort()
    assert isinstance(store, StoragePort)
    store.save("k1", "v1")
    assert store.load("k1") == "v1"
    assert store.load("missing") is None
    store.delete("k1")
    assert store.load("k1") is None


def test_mock_event_store_satisfies_protocol():
    """InMemoryEventStore 必须满足 EventStorePort。"""
    from lingwen_core.ports.storage import EventStorePort, InMemoryEventStore, DomainEvent

    store: EventStorePort = InMemoryEventStore()
    assert isinstance(store, EventStorePort)

    class SampleEvent(DomainEvent):
        type: str = "sample"
        payload: dict = {}

    e1 = SampleEvent(payload={"x": 1})
    store.append(e1)
    events = list(store.replay(since=0))
    assert len(events) == 1
    assert events[0].payload == {"x": 1}


def test_mock_llm_satisfies_protocol():
    """EchoLLM 必须满足 LLMPort。"""
    from lingwen_core.ports.llm import LLMPort, EchoLLM

    llm: LLMPort = EchoLLM()
    assert isinstance(llm, LLMPort)
    assert llm.complete("hello") == "hello"
    assert llm.complete("world", tier="fast") == "world"


def test_mock_embedding_satisfies_protocol():
    """HashEmbedding 必须满足 EmbeddingPort。"""
    from lingwen_core.ports.llm import EmbeddingPort, HashEmbedding

    emb: EmbeddingPort = HashEmbedding()
    assert isinstance(emb, EmbeddingPort)
    v1 = emb.embed("hello")
    v2 = emb.embed("hello")
    assert v1 == v2  # 同一输入产生相同向量
    assert len(v1) == 16  # 默认 16 维
    v3 = emb.embed("world")
    assert v1 != v3  # 不同输入产生不同向量


def test_mock_checker_satisfies_protocol():
    """AlwaysPassChecker 必须满足 CheckerPort。"""
    from lingwen_core.ports.checker import CheckerPort, AlwaysPassChecker

    checker: CheckerPort = AlwaysPassChecker()
    assert isinstance(checker, CheckerPort)
    # 最小冒烟：传 None 应返回 list（空问题列表）
    issues = checker.check(None)  # type: ignore[arg-type]
    assert isinstance(issues, list)


def test_ports_init_exports_all():
    """lingwen_core.ports.__init__ 应暴露所有 Protocol 和 Mock。"""
    import lingwen_core.ports as ports

    for name in [
        "StoragePort",
        "EventStorePort",
        "LLMPort",
        "EmbeddingPort",
        "CheckerPort",
        "DomainEvent",
        "InMemoryStoragePort",
        "InMemoryEventStore",
        "EchoLLM",
        "HashEmbedding",
        "AlwaysPassChecker",
    ]:
        assert hasattr(ports, name), f"missing export: {name}"