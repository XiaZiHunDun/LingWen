"""Tests for prompt_engineering.extraction (Phase 2.1 — LLM ripple extraction).

Doc 1 §3.4 + Doc 2 §6 联动:解析 LLM 输出的 ripple_extraction JSON,
供 RippleEngine.register 批量使用。

API:
- ExtractedRipple: 新涟漪(待 register)
- ExtractedResolution: 已平复(待 resolve)
- RippleExtractionResult: 完整结果
- parse_ripple_extraction(raw_llm_output: str) → RippleExtractionResult
- ExtractionParseError: 解析失败 (非 JSON / 缺字段)

JSON 容忍:
- 纯 JSON:`{"new_ripples": [...], "resolved_ripples": [...]}`
- markdown 包装:` ```json\\n{...}\\n``` `
"""
from __future__ import annotations

import pytest

from infra.prompt_engineering.extraction import (
    ExtractedResolution,
    ExtractedRipple,
    ExtractionParseError,
    RippleExtractionResult,
    parse_ripple_extraction,
)

# === TestParsePlainJSON ===

class TestParsePlainJSON:
    """纯 JSON 输入(无 markdown 包装)"""

    def test_empty_result(self):
        raw = '{"new_ripples": [], "resolved_ripples": []}'
        result = parse_ripple_extraction(raw)
        assert result.new_ripples == ()
        assert result.resolved_ripples == ()
        assert result.notes == ""

    def test_single_new_ripple(self):
        raw = '''{
            "new_ripples": [
                {"ripple_id": "r1", "origin_event": "林尘身世", "origin_ch": 10}
            ],
            "resolved_ripples": []
        }'''
        result = parse_ripple_extraction(raw)
        assert len(result.new_ripples) == 1
        r = result.new_ripples[0]
        assert r.ripple_id == "r1"
        assert r.origin_event == "林尘身世"
        assert r.origin_ch == 10

    def test_multiple_new_ripples(self):
        raw = '''{
            "new_ripples": [
                {"ripple_id": "r1", "origin_event": "e1", "origin_ch": 10},
                {"ripple_id": "r2", "origin_event": "e2", "origin_ch": 20},
                {"ripple_id": "r3", "origin_event": "e3", "origin_ch": 30}
            ],
            "resolved_ripples": []
        }'''
        result = parse_ripple_extraction(raw)
        assert len(result.new_ripples) == 3
        assert {r.ripple_id for r in result.new_ripples} == {"r1", "r2", "r3"}

    def test_single_resolved_ripple(self):
        raw = '''{
            "new_ripples": [],
            "resolved_ripples": [
                {"ripple_id": "r1", "resolution_ch": 200, "mode": "strong"}
            ]
        }'''
        result = parse_ripple_extraction(raw)
        assert len(result.resolved_ripples) == 1
        r = result.resolved_ripples[0]
        assert r.ripple_id == "r1"
        assert r.resolution_ch == 200
        assert r.mode == "strong"

    def test_full_with_optional_fields(self):
        raw = '''{
            "new_ripples": [
                {
                    "ripple_id": "r1",
                    "origin_event": "e1",
                    "origin_ch": 10,
                    "affected_nodes": ["character:林尘", "character:暗皇"],
                    "planned_resolve_ch": 200,
                    "decay_rate": 0.3
                }
            ],
            "resolved_ripples": [
                {"ripple_id": "r0", "resolution_ch": 100, "mode": "weak"}
            ],
            "notes": "本章挖坑 1 个,平复 1 个"
        }'''
        result = parse_ripple_extraction(raw)
        assert len(result.new_ripples) == 1
        r = result.new_ripples[0]
        assert r.affected_nodes == ("character:林尘", "character:暗皇")
        assert r.planned_resolve_ch == 200
        assert r.decay_rate == 0.3
        assert len(result.resolved_ripples) == 1
        assert result.resolved_ripples[0].mode == "weak"
        assert result.notes == "本章挖坑 1 个,平复 1 个"


# === TestParseMarkdownWrapped ===

class TestParseMarkdownWrapped:
    """markdown ```json ... ``` 包装 → 自动 strip"""

    def test_strips_json_markdown_block(self):
        raw = '''```json
{
    "new_ripples": [
        {"ripple_id": "r1", "origin_event": "e", "origin_ch": 10}
    ],
    "resolved_ripples": []
}
```'''
        result = parse_ripple_extraction(raw)
        assert len(result.new_ripples) == 1
        assert result.new_ripples[0].ripple_id == "r1"

    def test_strips_plain_code_block(self):
        """无 json 标识的 ``` 包装也处理"""
        raw = '''```
{"new_ripples": [], "resolved_ripples": []}
```'''
        result = parse_ripple_extraction(raw)
        assert result.new_ripples == ()
        assert result.resolved_ripples == ()

    def test_strips_with_surrounding_text(self):
        """LLM 经常在 JSON 前后加说明文字"""
        raw = '''以下是提取结果:

```json
{"new_ripples": [{"ripple_id": "r1", "origin_event": "e", "origin_ch": 10}], "resolved_ripples": []}
```

如有疑问请联系。'''
        result = parse_ripple_extraction(raw)
        assert len(result.new_ripples) == 1


# === TestParseErrors ===

class TestParseErrors:
    """解析错误情况"""

    def test_invalid_json_raises(self):
        with pytest.raises(ExtractionParseError):
            parse_ripple_extraction("not valid json at all")

    def test_missing_new_ripples_field_raises(self):
        # 缺 new_ripples 字段 → 应抛错(用 get 默认值会掩盖错误)
        with pytest.raises(ExtractionParseError):
            parse_ripple_extraction('{"resolved_ripples": []}')

    def test_missing_ripple_id_in_new_raises(self):
        with pytest.raises(ExtractionParseError):
            parse_ripple_extraction(
                '{"new_ripples": [{"origin_event": "e", "origin_ch": 10}], "resolved_ripples": []}'
            )

    def test_missing_origin_ch_in_new_raises(self):
        with pytest.raises(ExtractionParseError):
            parse_ripple_extraction(
                '{"new_ripples": [{"ripple_id": "r1", "origin_event": "e"}], "resolved_ripples": []}'
            )

    def test_missing_mode_in_resolved_raises(self):
        with pytest.raises(ExtractionParseError):
            parse_ripple_extraction(
                '{"new_ripples": [], "resolved_ripples": [{"ripple_id": "r1", "resolution_ch": 100}]}'
            )


# === TestDataclasses ===

class TestDataclasses:
    """dataclass 不可变 + 字段语义"""

    def test_extracted_ripple_frozen(self):
        r = ExtractedRipple(ripple_id="r1", origin_event="e", origin_ch=10)
        with pytest.raises((AttributeError, Exception)):
            r.ripple_id = "r2"  # type: ignore[misc]

    def test_extracted_resolution_frozen(self):
        r = ExtractedResolution(ripple_id="r1", resolution_ch=100, mode="strong")
        with pytest.raises((AttributeError, Exception)):
            r.mode = "weak"  # type: ignore[misc]

    def test_result_frozen(self):
        res = RippleExtractionResult()
        with pytest.raises((AttributeError, Exception)):
            res.notes = "x"  # type: ignore[misc]

    def test_ripple_defaults(self):
        """可选字段默认值"""
        r = ExtractedRipple(ripple_id="r1", origin_event="e", origin_ch=10)
        assert r.affected_nodes == ()
        assert r.planned_resolve_ch is None
        assert r.decay_rate == 0.2


# === TestImportContract ===

class TestImportContract:
    """Public API 完整性"""

    def test_top_level_imports(self):
        from infra.prompt_engineering import (
            ExtractedResolution,
            ExtractedRipple,
            ExtractionParseError,
            RippleExtractionResult,
            parse_ripple_extraction,
        )
        assert ExtractedRipple is not None
        assert ExtractedResolution is not None
        assert RippleExtractionResult is not None
        assert callable(parse_ripple_extraction)
        assert issubclass(ExtractionParseError, Exception)
