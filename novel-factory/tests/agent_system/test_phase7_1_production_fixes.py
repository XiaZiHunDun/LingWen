"""Phase 7.1 回归测试 — 覆盖修复点 1+3 + 韧性契约

- Fix #1: master.audit_chapter 内部必须调 auditor.audit_chapter (不是 llm_audit)
- Fix #3: _handler_chapter_review 返回值必须含 content 字段 (供下游 polish 用)
- 韧性:    audit_chapter 抛错不应让 workflow 崩溃 (master.audit_chapter 已有 try/except)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.agent_system.got_bridge import _handler_chapter_review
from infra.agent_system.master_controller import MasterController
from tests.agent_system._e2e_helpers import (
    make_master_with_router,
    make_stub_router,
    make_stub_router_with_responses,
)


def test_master_audit_chapter_calls_auditor_audit_chapter(monkeypatch, tmp_path):
    """Fix #1 回归: master.audit_chapter → self.auditor.audit_chapter (不是 llm_audit)

    不替换 master 方法,只 monkeypatch self.auditor.audit_chapter 记录调用。
    修复前: master.audit_chapter 调 self.auditor.llm_audit(...) → AttributeError,
            被 try/except 吞,master.audit_chapter 仍返回,但 called 列表为空。
    修复后: master.audit_chapter 调 self.auditor.audit_chapter(...) → called 列表非空。
    """
    router, providers = make_stub_router()
    master = make_master_with_router(tmp_path, router)

    called = []

    def fake_audit_chapter(chapter_num, content, characters, context, reviewer_id=None):
        called.append({
            "chapter_num": chapter_num,
            "content": content,
            "reviewer_id": reviewer_id,
            "context": context,
        })
        return {"issues": [], "scores": {"S1": 8, "S2": 8}}

    monkeypatch.setattr(master.auditor, "audit_chapter", fake_audit_chapter)

    master.audit_chapter(
        chapter_num=1,
        content="第一章正文 100 字",
        characters=[],
        timeline=["事件 A", "事件 B"],
    )

    # master.audit_chapter 调 generate_audit_report 包装, 验证 fake 被调过
    assert len(called) == 1, f"expected 1 call, got {len(called)}"
    assert called[0]["chapter_num"] == 1
    assert called[0]["content"] == "第一章正文 100 字"
    assert called[0]["reviewer_id"] is None  # 默认 None
    assert "timeline" in called[0]["context"]


def test_review_handler_propagates_content_to_downstream():
    """Fix #3 回归: _handler_chapter_review 返回 dict 必须含 content 字段

    不跑完整 workflow,直接调 _handler_chapter_review,验证返回值的 content 键
    等于 inputs["content"]。下游 _handler_polish 读 inputs["content"] 拿不到会
    return {"_error": "content is required"} 中断。

    使用 MasterController.__new__ 跳过 __init__,handler 只调 master.audit_chapter
    (我们在外部 stub 掉),不依赖完整 controller 状态。
    """
    master = MasterController.__new__(MasterController)

    # stub master.audit_chapter 返回 audit report (无 content 字段)
    master.audit_chapter = lambda **kwargs: {
        "chapter_num": kwargs.get("chapter_num"),
        "issues": [],
        "scores": {"S1": 8},
    }

    result = _handler_chapter_review(
        master=master,
        inputs={
            "chapter_num": 1,
            "content": "原始正文 100 字",
            "characters": [],
            "timeline": [],
        },
    )

    # 关键断言: result 必须含 content 字段 (修复前会缺失)
    assert "content" in result, f"handler result missing 'content': {result}"
    assert result["content"] == "原始正文 100 字"
    # 不破坏 audit 报告其他字段
    assert result["issues"] == []
    assert result["scores"] == {"S1": 8}


def test_audit_chapter_failure_does_not_crash_workflow(tmp_path: Path):
    """韧性契约: audit_chapter 抛错被 master.audit_chapter try/except 兜住,workflow 仍 COMPLETED

    这个测试不依赖 fix #1 是否存在 (修复前/后都 pass):
    - 修复前: llm_audit AttributeError 被 master.audit_chapter except 吞,无 LLM 调用
    - 修复后: audit_chapter 内部 RuntimeError 被 master.audit_chapter except 吞,有 1 次 LLM 调用

    两种路径都验证 "audit 失败非致命" 契约。目的是把这条契约写进回归保护,
    防止未来重构破坏 master.audit_chapter 的 try/except 行为。
    """
    from infra.got.data_structures import NodeStatus

    # StubProvider 默认返回固定 response,我们要让它在第 2 次 LLM 调用时抛错
    # minimal_e2e 节点顺序: write (1 LLM) → review (1 LLM via audit_chapter)
    router, providers = make_stub_router_with_responses({"anthropic": "stub-response"})
    # 覆盖 anthropic provider 的 generate 方法,让它在第 2 次调用时 raise
    original_generate = providers["anthropic"].generate
    call_count = [0]

    def flaky_generate(prompt, **kwargs):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise RuntimeError("simulated audit failure")
        return original_generate(prompt, **kwargs)

    providers["anthropic"].generate = flaky_generate

    master = make_master_with_router(tmp_path, router)
    result = master.run_workflow(
        workflow_name="minimal_e2e",
        initial_inputs={
            "chapter_num": 1,
            "outline": {"chapters": [{"num": 1, "title": "第一章", "events": ["e1"]}]},
            "characters": [],
            "memory_context": {},
            "style_guide": {},
            "use_llm": True,
        },
    )

    # 关键契约: workflow 不因 audit 失败而崩溃
    assert result["summary"].failed == 0
    assert result["summary"].completed == 2  # write + review 都 COMPLETED
    # review 节点的 audit 报告 issues 列表可能为空 (LLM 调用失败被吞)
    review_ex = result["executions"]["review"]
    assert review_ex.status == NodeStatus.COMPLETED
