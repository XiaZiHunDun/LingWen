#!/usr/bin/env python3
"""
单元测试: Inspector / Repairer 框架

覆盖:
- Inspector 基类: check() abstract, check_batch(), read_chapter(), get_chapter_context()
- Issue dataclass: 默认值 + 严重性归一化 (Enum → str)
- RuleBasedInspector: 按规则生成 Issue
- LLMBasedInspector: lazy 加载 LLMService
- Repairer 抽象基类 (R4-005): 无法直接实例化
- RuleBasedRepairer: 替换 + 写入回退
- YAMLRuleRepairer: YAML 加载 + deletion 规则 + 缺失文件容错
- WorldviewChecker / AITraceChecker: 集成测试
- WorldviewRepairer / AITraceRepairer: YAML 驱动集成测试

隔离策略:
- 通过 isolated_paths fixture 替换 ProjectPaths._instance 为 tmp_path-based 实例
- 任何 repairer 写操作都落到 tmp_path
"""

import pytest
import sys
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.paths import ProjectPaths
from infra.quality import (
    Inspector, Issue, RuleBasedInspector, LLMBasedInspector,
    Repairer, RepairResult, RuleBasedRepairer, YAMLRuleRepairer,
    WorldviewChecker, AITraceChecker,
    WorldviewRepairer, AITraceRepairer,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def isolated_paths(monkeypatch, tmp_path):
    """
    隔离 ProjectPaths 单例到 tmp_path。

    重建目录结构:
        tmp_path/
        ├── 03_内容仓库/04_正文/        (chapters)
        ├── 03_内容仓库/角色设定/      (characters, 含 character_profiles.json 占位)
        └── tools/rules/                (rules)
    """
    # 重置单例
    ProjectPaths._instance = None

    # 创建必需的目录
    chapters_dir = tmp_path / "03_内容仓库" / "04_正文"
    characters_dir = tmp_path / "03_内容仓库" / "角色设定"
    rules_dir = tmp_path / "tools" / "rules"
    for d in (chapters_dir, characters_dir, rules_dir):
        d.mkdir(parents=True)

    # 创建 character_profiles.json 占位（ProjectPaths._validate 要求）
    (characters_dir / "character_profiles.json").write_text(
        '{"characters": []}', encoding="utf-8"
    )

    paths = ProjectPaths.get(tmp_path)
    yield paths, chapters_dir, rules_dir

    # 清理: 重置单例以便其他测试不互相污染
    ProjectPaths._instance = None


def _write_chapter(chapters_dir: Path, num: int, content: str) -> Path:
    path = chapters_dir / f"ch{num:03d}.md"
    path.write_text(content, encoding="utf-8")
    return path


def _write_rules(rules_dir: Path, name: str, rules: list) -> Path:
    path = rules_dir / name
    payload = {"version": "1.0", "rules": rules}
    path.write_text(yaml.safe_dump(payload, allow_unicode=True), encoding="utf-8")
    return path


# ============================================================================
# Issue dataclass
# ============================================================================

class TestIssueDataclass:
    """Issue dataclass 默认值 + 严重性归一化"""

    def test_minimal_construction(self):
        """仅传必填字段,其他走默认"""
        issue = Issue(
            chapter=1,
            dimension="d",
            issue_type="t",
            severity="P0",
            description="x",
        )
        assert issue.chapter == 1
        assert issue.location == ""
        assert issue.evidence == ""
        assert issue.suggestion == ""

    def test_severity_normalized_from_enum(self):
        """传入 IssueSeverity 枚举 → __post_init__ 归一化为 str"""
        from infra.consistency.engine.data_structures import IssueSeverity
        issue = Issue(
            chapter=2,
            dimension="d",
            issue_type="t",
            severity=IssueSeverity.P0,
            description="x",
        )
        # P0 归一化后是 "P0" 或 "0"，但一定是 str 类型
        assert isinstance(issue.severity, str)
        assert not hasattr(issue.severity, "value")


# ============================================================================
# Inspector 基类
# ============================================================================

class TestInspectorBase:
    """Inspector 抽象行为"""

    def test_cannot_call_check_directly(self, isolated_paths):
        """Inspector.check() 必须被子类实现,基类调用抛 NotImplementedError"""
        paths, _, _ = isolated_paths
        inspector = Inspector(paths=paths)
        with pytest.raises(NotImplementedError):
            inspector.check(1)

    def test_read_chapter_existing(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "# ch1\nbody")
        inspector = Inspector(paths=paths)
        assert inspector.read_chapter(1) == "# ch1\nbody"

    def test_read_chapter_missing(self, isolated_paths):
        paths, _, _ = isolated_paths
        inspector = Inspector(paths=paths)
        assert inspector.read_chapter(9999) == ""

    def test_check_batch_aggregates(self, isolated_paths):
        """check_batch 应调用每个章节的 check(),并合并所有 issues"""
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "alpha")
        _write_chapter(chapters_dir, 2, "alpha beta")
        _write_chapter(chapters_dir, 3, "alpha beta gamma")

        class CountingInspector(Inspector):
            def check(self, chapter_num):
                content = self.read_chapter(chapter_num)
                # 每章节产 1 个 Issue,description 含词数
                return [Issue(
                    chapter=chapter_num,
                    dimension="d",
                    issue_type="t",
                    severity="P0",
                    description=str(len(content.split())),
                )]

        inspector = CountingInspector(paths=paths)
        results = inspector.check_batch([1, 2, 3])
        assert len(results) == 3
        assert [r.chapter for r in results] == [1, 2, 3]
        assert [r.description for r in results] == ["1", "2", "3"]

    def test_get_chapter_context_includes_neighbors(self, isolated_paths):
        """get_chapter_context 应包含前后文,但跳过章节自身"""
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "ch1 content")
        _write_chapter(chapters_dir, 2, "ch2 content")
        _write_chapter(chapters_dir, 3, "ch3 content")
        inspector = Inspector(paths=paths)
        ctx = inspector.get_chapter_context(2, before=1, after=1)
        assert 1 in ctx
        assert 3 in ctx
        assert 2 not in ctx  # 自身排除
        assert "ch1 content" in ctx[1]
        assert "ch3 content" in ctx[3]


# ============================================================================
# RuleBasedInspector
# ============================================================================

class TestRuleBasedInspector:
    def test_no_rules_returns_empty(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "anything goes")
        insp = RuleBasedInspector(rules=[], paths=paths)
        assert insp.check(1) == []

    def test_rule_match_generates_issue(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "badword badword appears twice")
        insp = RuleBasedInspector(
            rules=["badword"],
            paths=paths,
        )
        # 设置 class-level 字段 (RuleBasedInspector 假设子类提供)
        insp.dimension = "维度"
        insp.issue_type = "类型"
        issues = insp.check(1)
        assert len(issues) == 1
        assert issues[0].severity == "P2"
        assert "2" in issues[0].description  # count=2 (badword 出现2次)
        assert issues[0].chapter == 1

    def test_missing_chapter_returns_empty(self, isolated_paths):
        paths, _, _ = isolated_paths
        insp = RuleBasedInspector(rules=["x"], paths=paths)
        assert insp.check(9999) == []


# ============================================================================
# LLMBasedInspector (lazy load)
# ============================================================================

class TestLLMBasedInspector:
    def test_check_raises_not_implemented(self, isolated_paths):
        paths, _, _ = isolated_paths
        insp = LLMBasedInspector(paths=paths)
        with pytest.raises(NotImplementedError):
            insp.check(1)

    def test_llm_service_lazy_loaded(self, isolated_paths, monkeypatch):
        """首次访问 .llm_service 才会创建 LLMService 实例"""
        paths, _, _ = isolated_paths

        # 桩: 预加载 infra.llm_service 模块,然后 patch LLMService.get
        # (LLMBasedInspector 在 property 内 import,模块不会直接持有引用)
        import infra.llm_service as llm_mod
        sentinel = MagicMock(name="LLMServiceSentinel")
        monkeypatch.setattr(llm_mod, "LLMService", MagicMock(get=MagicMock(return_value=sentinel)))

        # 重置可能的缓存
        insp = LLMBasedInspector(paths=paths)
        insp._llm_service = None

        svc = insp.llm_service
        assert svc is sentinel
        # 第二次访问应复用缓存（不会再调用 LLMService.get）
        svc2 = insp.llm_service
        assert svc2 is sentinel


# ============================================================================
# Repairer 抽象基类 (R4-005)
# ============================================================================

class TestRepairerAbstract:
    def test_cannot_instantiate_directly(self, isolated_paths):
        """R4-005: Repairer 标记 abstract,不能直接 Repairer()"""
        paths, _, _ = isolated_paths
        with pytest.raises(TypeError):
            Repairer(paths=paths)

    def test_concrete_subclass_works(self, isolated_paths):
        """实现了两个 abstractmethod 后可以实例化"""
        paths, _, _ = isolated_paths

        class MinimalRepairer(Repairer):
            def _apply_rules(self, content, issues):
                return content, 0

            def _get_rules(self):
                return []

        r = MinimalRepairer(paths=paths)
        assert r is not None

    def test_repair_missing_chapter_returns_error(self, isolated_paths):
        paths, _, _ = isolated_paths

        class NoopRepairer(Repairer):
            def _apply_rules(self, content, issues):
                return content, 0

            def _get_rules(self):
                return []

        r = NoopRepairer(paths=paths)
        result = r.repair(9999)
        assert result.success is False
        assert "不存在" in result.error
        assert result.changes == 0

    def test_repair_batch_returns_dict(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "alpha")
        _write_chapter(chapters_dir, 2, "beta")

        class NoopRepairer(Repairer):
            def _apply_rules(self, content, issues):
                return content, 0

            def _get_rules(self):
                return []

        r = NoopRepairer(paths=paths)
        results = r.repair_batch([1, 2])
        assert set(results.keys()) == {1, 2}
        assert all(res.success for res in results.values())

    def test_dry_run_does_not_write(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        chapter = _write_chapter(chapters_dir, 1, "alpha old")
        original = chapter.read_text(encoding="utf-8")

        class RenamingRepairer(Repairer):
            def _apply_rules(self, content, issues):
                return content.replace("old", "new"), 1

            def _get_rules(self):
                return []

        r = RenamingRepairer(paths=paths)
        preview = r.dry_run(1)
        assert preview == "alpha new"
        # 磁盘内容未变
        assert chapter.read_text(encoding="utf-8") == original


# ============================================================================
# RuleBasedRepairer
# ============================================================================

class TestRuleBasedRepairer:
    def test_replace_all_occurrences(self, isolated_paths):
        paths, _, _ = isolated_paths
        rules = [("foo", "bar", "x→y"), ("baz", "qux", "a→b")]
        r = RuleBasedRepairer(rules=rules, paths=paths)
        new, count = r._apply_rules("foo foo baz", [])
        assert new == "bar bar qux"
        assert count == 3  # 2 foo + 1 baz

    def test_no_match_returns_zero(self, isolated_paths):
        paths, _, _ = isolated_paths
        r = RuleBasedRepairer(rules=[("foo", "bar", "x")], paths=paths)
        new, count = r._apply_rules("nothing here", [])
        assert new == "nothing here"
        assert count == 0

    def test_repair_writes_only_when_changed(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        chapter = _write_chapter(chapters_dir, 1, "foo here")
        rules = [("foo", "bar", "x")]
        r = RuleBasedRepairer(rules=rules, paths=paths)

        result = r.repair(1)
        assert result.success is True
        assert result.changes == 1
        assert chapter.read_text(encoding="utf-8") == "bar here"

    def test_repair_skips_write_when_no_change(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        chapter = _write_chapter(chapters_dir, 1, "no match here")
        original = chapter.read_text(encoding="utf-8")
        rules = [("foo", "bar", "x")]
        r = RuleBasedRepairer(rules=rules, paths=paths)

        result = r.repair(1)
        assert result.changes == 0
        assert chapter.read_text(encoding="utf-8") == original

    def test_get_rules_returns_custom_when_provided(self, isolated_paths):
        paths, _, _ = isolated_paths
        rules = [("a", "b", "desc")]
        r = RuleBasedRepairer(rules=rules, paths=paths)
        assert r._get_rules() == rules

    def test_get_rules_empty_when_none(self, isolated_paths):
        paths, _, _ = isolated_paths
        r = RuleBasedRepairer(rules=None, paths=paths)
        assert r._get_rules() == []


# ============================================================================
# YAMLRuleRepairer
# ============================================================================

class TestYAMLRuleRepairer:
    def test_load_missing_file_returns_empty(self, isolated_paths):
        """rules_file 不存在时 _load_rules 返回 []"""
        paths, _, _ = isolated_paths
        r = YAMLRuleRepairer(rules_file="nope.yaml", paths=paths)
        assert r._load_rules() == []

    def test_load_replacement_rule(self, isolated_paths):
        paths, _, rules_dir = isolated_paths
        _write_rules(rules_dir, "t.yaml", [
            {"type": "replacement", "source": "foo", "target": "bar", "description": "x"},
        ])
        r = YAMLRuleRepairer(rules_file="t.yaml", paths=paths)
        assert r._get_rules() == [("foo", "bar", "x")]

    def test_deletion_rule_has_empty_target(self, isolated_paths):
        """type: deletion 时,target 应被强制设为空串"""
        paths, _, rules_dir = isolated_paths
        _write_rules(rules_dir, "t.yaml", [
            {"type": "deletion", "source": "bad", "description": "remove bad word"},
        ])
        r = YAMLRuleRepairer(rules_file="t.yaml", paths=paths)
        rules = r._get_rules()
        assert rules == [("bad", "", "remove bad word")]

    def test_skip_rule_without_source(self, isolated_paths):
        """source 为空的规则应被过滤"""
        paths, _, rules_dir = isolated_paths
        _write_rules(rules_dir, "t.yaml", [
            {"type": "replacement", "source": "", "target": "x", "description": "skip"},
            {"type": "replacement", "source": "ok", "target": "y", "description": "keep"},
        ])
        r = YAMLRuleRepairer(rules_file="t.yaml", paths=paths)
        assert r._get_rules() == [("ok", "y", "keep")]

    def test_apply_rules_counts_occurrences(self, isolated_paths):
        paths, _, rules_dir = isolated_paths
        _write_rules(rules_dir, "t.yaml", [
            {"type": "replacement", "source": "x", "target": "y", "description": ""},
        ])
        r = YAMLRuleRepairer(rules_file="t.yaml", paths=paths)
        new, count = r._apply_rules("xxx and x", [])
        assert new == "yyy and y"
        assert count == 4

    def test_rules_cache(self, isolated_paths):
        """二次调用 _load_rules 应使用缓存"""
        paths, _, rules_dir = isolated_paths
        _write_rules(rules_dir, "t.yaml", [
            {"type": "replacement", "source": "a", "target": "b", "description": ""},
        ])
        r = YAMLRuleRepairer(rules_file="t.yaml", paths=paths)
        first = r._load_rules()
        second = r._load_rules()
        assert first is second  # 同一对象

    def test_repair_writes_when_changed(self, isolated_paths):
        paths, chapters_dir, rules_dir = isolated_paths
        _write_chapter(chapters_dir, 1, "old text")
        _write_rules(rules_dir, "t.yaml", [
            {"type": "replacement", "source": "old", "target": "new", "description": ""},
        ])
        r = YAMLRuleRepairer(rules_file="t.yaml", paths=paths)
        result = r.repair(1)
        assert result.success is True
        assert result.changes == 1
        assert (chapters_dir / "ch001.md").read_text(encoding="utf-8") == "new text"


# ============================================================================
# WorldviewChecker 集成测试
# ============================================================================

class TestWorldviewChecker:
    def test_detects_scifi_term(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "飞船在核废土上飞过")
        checker = WorldviewChecker(paths=paths)
        issues = checker.check(1)
        # 至少检出 "核废土" 和 "飞船"
        types = {i.evidence for i in issues}
        assert any("核废土" in t for t in types)
        assert any("飞船" in t for t in types)

    def test_clean_chapter_no_issue(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "林夜盘膝而坐，灵气涌入丹田。")
        checker = WorldviewChecker(paths=paths)
        assert checker.check(1) == []

    def test_severity_is_p1(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "飞船")
        checker = WorldviewChecker(paths=paths)
        issues = checker.check(1)
        assert all(i.severity == "P1" for i in issues)

    def test_missing_chapter(self, isolated_paths):
        paths, _, _ = isolated_paths
        checker = WorldviewChecker(paths=paths)
        assert checker.check(9999) == []


# ============================================================================
# AITraceChecker 集成测试
# ============================================================================

class TestAITraceChecker:
    def test_detects_ai_pattern(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "首先，他看着窗外。其次，雨水落下。")
        checker = AITraceChecker(paths=paths)
        issues = checker.check(1)
        assert any("首先" in i.evidence for i in issues)
        assert any("其次" in i.evidence for i in issues)

    def test_clean_chapter_no_issue(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "雨落下来，打湿了地面。")
        checker = AITraceChecker(paths=paths)
        assert checker.check(1) == []

    def test_severity_is_p2(self, isolated_paths):
        paths, chapters_dir, _ = isolated_paths
        _write_chapter(chapters_dir, 1, "首先")
        checker = AITraceChecker(paths=paths)
        assert all(i.severity == "P2" for i in checker.check(1))


# ============================================================================
# WorldviewRepairer 集成测试 (使用真实 YAML)
# ============================================================================

class TestWorldviewRepairer:
    def test_replaces_scifi_term_via_real_yaml(self, isolated_paths):
        """复制 tools/rules/worldview_rules.yaml 到 tmp_path,跑修复"""
        paths, chapters_dir, rules_dir = isolated_paths

        # 复制真实 YAML 到 tmp_path
        real_yaml = PROJECT_ROOT / "tools" / "rules" / "worldview_rules.yaml"
        target_yaml = rules_dir / "worldview_rules.yaml"
        target_yaml.write_text(real_yaml.read_text(encoding="utf-8"), encoding="utf-8")

        _write_chapter(chapters_dir, 1, "核废土上的飞船起飞了")
        r = WorldviewRepairer(paths=paths)
        result = r.repair(1)
        assert result.success is True
        assert result.changes > 0
        new_text = (chapters_dir / "ch001.md").read_text(encoding="utf-8")
        assert "核废土" not in new_text
        assert "飞船" not in new_text
        # 修真术语应在
        assert "灵气衰竭区域" in new_text

    def test_dry_run_no_write(self, isolated_paths):
        paths, chapters_dir, rules_dir = isolated_paths
        real_yaml = PROJECT_ROOT / "tools" / "rules" / "worldview_rules.yaml"
        (rules_dir / "worldview_rules.yaml").write_text(
            real_yaml.read_text(encoding="utf-8"), encoding="utf-8"
        )
        chapter = _write_chapter(chapters_dir, 1, "飞船起飞")
        original = chapter.read_text(encoding="utf-8")
        r = WorldviewRepairer(paths=paths)
        preview = r.dry_run(1)
        assert "灵舟" in preview  # 假设 worldview_rules.yaml 含飞船→灵舟
        # 磁盘未变
        assert chapter.read_text(encoding="utf-8") == original


# ============================================================================
# AITraceRepairer 集成测试 (使用真实 YAML)
# ============================================================================

class TestAITraceRepairer:
    def test_deletion_rule_removes_phrase(self, isolated_paths):
        """ai_trace_rules.yaml 里的 deletion 类型规则应清空目标短语"""
        paths, chapters_dir, rules_dir = isolated_paths

        real_yaml = PROJECT_ROOT / "tools" / "rules" / "ai_trace_rules.yaml"
        (rules_dir / "ai_trace_rules.yaml").write_text(
            real_yaml.read_text(encoding="utf-8"), encoding="utf-8"
        )

        # 写一个肯定含 "首先" 的章节
        _write_chapter(chapters_dir, 1, "首先，林夜走入山谷。其次，天色渐暗。")
        r = AITraceRepairer(paths=paths)
        result = r.repair(1)
        # 至少处理了一些 (数量取决于 YAML 规则定义)
        new_text = (chapters_dir / "ch001.md").read_text(encoding="utf-8")
        # "首先" 应已被删除或替换
        assert "首先，" not in new_text or "首先" not in new_text


# ============================================================================
# RepairResult dataclass
# ============================================================================

class TestRepairResult:
    def test_defaults(self):
        rr = RepairResult(chapter=1, success=True)
        assert rr.changes == 0
        assert rr.new_content == ""
        assert rr.error == ""

    def test_error_path(self):
        rr = RepairResult(chapter=2, success=False, error="boom")
        assert rr.error == "boom"
        assert rr.success is False
