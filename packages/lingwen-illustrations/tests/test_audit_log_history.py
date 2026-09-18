"""Phase 99: audit_log id kwarg backward-compat + read_history pagination."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from lingwen_illustrations import audit_log
from lingwen_illustrations.metadata import IllustrationMetadata


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    (tmp_path / ".lingwen").mkdir(parents=True, exist_ok=True)
    return tmp_path


def _meta(id: str = "asset-1", type: str = "cover", chapter_num: int | None = None) -> IllustrationMetadata:
    return IllustrationMetadata(
        id=id,
        type=type,  # type: ignore[arg-type]
        project_slug="proj",
        chapter_num=chapter_num,
        style_preset="ink",
        custom_prompt=None,
        scene_json={"scene": "test"},
        final_prompt="a test illustration",
        prompt_hash="abc123",
        model="minimax-multimodal",
        created_at="2026-09-18T07:00:00+00:00",
        provider="minimax",
    )


def test_record_event_without_id_stays_unchanged(tmp_path: Path) -> None:
    """Backward-compat: existing callers (Phase 98 A1-A4) pass no id."""
    root = tmp_path
    audit_log.record_event(root, event="generation", asset_meta=_meta())
    line = (root / ".lingwen" / "illustration_audit.jsonl").read_text().strip()
    payload = json.loads(line)
    assert "id" not in payload  # Phase 99 must NOT inject id when caller doesn't pass


def test_record_event_with_id_writes_id(tmp_path: Path) -> None:
    root = tmp_path
    audit_log.record_event(root, event="generation", asset_meta=_meta(), id="01HZX7K3ABC")
    line = (root / ".lingwen" / "illustration_audit.jsonl").read_text().strip()
    payload = json.loads(line)
    assert payload["id"] == "01HZX7K3ABC"


def test_read_history_empty_file_returns_empty(tmp_path: Path) -> None:
    root = tmp_path
    events, has_more = audit_log.read_history(root, since_id=None, limit=10)
    assert events == []
    assert has_more is False


def test_read_history_filters_by_id_and_paginates(tmp_path: Path) -> None:
    """Pagination semantics (Phase 99 I091): SSE catch-up — return events
    NEWER than since_id (id > since_id), sorted most-recent first, with
    has_more=True when more rows exist beyond limit.
    """
    root = tmp_path
    for i in range(5):
        ulid_str = f"01HZX7K{str(i).zfill(19)}"
        audit_log.record_event(root, event="generation", asset_meta=_meta(id=f"asset-{i}"), id=ulid_str)
    # No since_id: get latest 3 (descending by id).
    events, has_more = audit_log.read_history(root, since_id=None, limit=3)
    assert has_more is True
    assert len(events) == 3
    assert events[0]["id"] == "01HZX7K0000000000000000004"
    assert events[-1]["id"] == "01HZX7K0000000000000000002"
    # since_id=...1 returns events strictly NEWER than ...1 (id > since_id):
    # for ULIDs "...2", "...3", "...4" — sorted desc.
    catchup, has_more2 = audit_log.read_history(root, since_id="01HZX7K0000000000000000001", limit=3)
    assert has_more2 is False
    assert len(catchup) == 3
    assert catchup[0]["id"] == "01HZX7K0000000000000000004"
    assert catchup[-1]["id"] == "01HZX7K0000000000000000002"
    # since_id at the highest id returns nothing.
    nothing_newer, has_more3 = audit_log.read_history(root, since_id="01HZX7K0000000000000000004", limit=3)
    assert has_more3 is False
    assert nothing_newer == []


def test_read_history_handles_corrupt_lines_gracefully(tmp_path: Path) -> None:
    root = tmp_path
    audit_log.record_event(root, event="generation", asset_meta=_meta(), id="01HZX7K0AAAAAAAAAAAAAAA0")
    audit_path = root / ".lingwen" / "illustration_audit.jsonl"
    with audit_path.open("a", encoding="utf-8") as f:
        f.write("not valid json {\n")
    events, _ = audit_log.read_history(root, since_id=None, limit=10)
    assert len(events) == 1  # corrupt line skipped
