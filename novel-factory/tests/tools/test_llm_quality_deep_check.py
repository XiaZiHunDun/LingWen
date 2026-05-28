# novel-factory/tests/tools/test_llm_quality_deep_check.py
"""
llm_quality_deep_check.py 测试

测试工具脚本的核心修复逻辑，不调用实际LLM API。
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestLLMQualityChecker:
    """LLMQualityChecker 核心方法测试"""

    @pytest.fixture
    def mock_llm_service(self):
        """模拟LLM服务，避免实际API调用"""
        with patch('tools.llm_quality_deep_check.LLMService') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def checker(self, mock_llm_service):
        """创建checker实例"""
        with patch('tools.llm_quality_deep_check.LLMService', return_value=mock_llm_service):
            # 延迟导入以避免环境问题
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from tools.llm_quality_deep_check import LLMQualityChecker
            return LLMQualityChecker(llm_service=mock_llm_service)

    def test_load_chapter(self, checker, tmp_path):
        """测试章节加载"""
        # 创建模拟章节文件
        project_root = tmp_path / "novel-factory"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        ch_file = chapters_dir / "ch001.md"
        ch_file.write_text("# 第一章测试内容", encoding='utf-8')

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        content = checker.load_chapter(1)
        assert content is not None
        assert "第一章测试内容" in content

    def test_load_chapter_not_found(self, checker, tmp_path):
        """测试加载不存在的章节"""
        project_root = tmp_path / "novel-factory"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        content = checker.load_chapter(999)
        assert content is None

    def test_load_chapters(self, checker, tmp_path):
        """测试批量章节加载"""
        project_root = tmp_path / "novel-factory"
        chapters_dir = project_root / "03_内容仓库" / "04_正文"
        chapters_dir.mkdir(parents=True)

        # 创建多个章节文件
        for i in range(1, 4):
            ch_file = chapters_dir / f"ch{i:03d}.md"
            ch_file.write_text(f"第{i}章内容", encoding='utf-8')

        checker.project_root = project_root
        checker.chapters_dir = chapters_dir

        result = checker.load_chapters([1, 2, 3])
        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_quality_report_creation(self, checker):
        """测试质检报告创建"""
        from tools.llm_quality_deep_check import QualityReport
        from infra.quality import Issue

        report = QualityReport(
            chapter=1,
            checker="test_checker",
            score=0.85
        )

        assert report.chapter == 1
        assert report.checker == "test_checker"
        assert report.score == 0.85
        assert report.llm_calls == 0
        assert report.timestamp != ""

    def test_quality_report_to_dict(self, checker):
        """测试质检报告序列化"""
        from tools.llm_quality_deep_check import QualityReport

        report = QualityReport(
            chapter=1,
            checker="test_checker",
            score=0.85
        )

        data = report.to_dict()
        assert data["chapter"] == 1
        assert data["checker"] == "test_checker"
        assert data["score"] == 0.85
        assert "timestamp" in data
        assert "issues" in data


class TestRepairMethods:
    """修复方法测试"""

    @pytest.fixture
    def mock_llm_service(self):
        with patch('tools.llm_quality_deep_check.LLMService') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def checker(self, mock_llm_service):
        with patch('tools.llm_quality_deep_check.LLMService', return_value=mock_llm_service):
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from tools.llm_quality_deep_check import LLMQualityChecker
            return LLMQualityChecker(llm_service=mock_llm_service)

    def test_repair_character_issue_signature(self, checker):
        """测试repair_character_issue方法签名"""
        from infra.quality import Issue

        issue = Issue(
            chapter=1,
            dimension="S9",
            issue_type="character_inconsistency",
            severity="P1",
            description="测试问题"
        )

        chapter_content = "测试章节内容"

        # 验证方法存在且可调用（不验证实际LLM调用）
        assert hasattr(checker, 'repair_character_issue')
        assert callable(checker.repair_character_issue)

    def test_repair_logic_issue_signature(self, checker):
        """测试repair_logic_issue方法签名"""
        from infra.quality import Issue

        issue = Issue(
            chapter=1,
            dimension="S2",
            issue_type="logic_contradiction",
            severity="P1",
            description="测试逻辑问题"
        )

        chapter_content = "测试章节内容"

        assert hasattr(checker, 'repair_logic_issue')
        assert callable(checker.repair_logic_issue)

    def test_repair_foreshadow_issue_signature(self, checker):
        """测试repair_foreshadow_issue方法签名"""
        from infra.quality import Issue

        issue = Issue(
            chapter=1,
            dimension="S11",
            issue_type="foreshadow_unresolved",
            severity="P2",
            description="测试伏笔问题"
        )

        chapter_content = "测试章节内容"

        assert hasattr(checker, 'repair_foreshadow_issue')
        assert callable(checker.repair_foreshadow_issue)


class TestComprehensiveQualityChecker:
    """综合质量检查器测试"""

    @pytest.fixture
    def mock_api_key(self):
        return "test_api_key_12345"

    def test_chapter_file_parsing(self, mock_api_key, tmp_path):
        """测试章节文件解析"""
        with patch('tools.comprehensive_quality_check.MiniMaxProvider'):
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from tools.comprehensive_quality_check import ComprehensiveQualityChecker

            checker = ComprehensiveQualityChecker(api_key=mock_api_key)

            # 设置测试目录
            project_root = tmp_path / "novel-factory"
            chapters_dir = project_root / "03_内容仓库" / "04_正文"
            chapters_dir.mkdir(parents=True)

            # 创建测试章节
            ch_file = chapters_dir / "ch001.md"
            ch_file.write_text("# 第一章\n测试内容", encoding='utf-8')

            checker.project_root = project_root

            files = checker.get_chapter_files()
            assert len(files) >= 1

    def test_read_chapter(self, mock_api_key, tmp_path):
        """测试读取章节内容"""
        with patch('tools.comprehensive_quality_check.MiniMaxProvider'):
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from tools.comprehensive_quality_check import ComprehensiveQualityChecker

            checker = ComprehensiveQualityChecker(api_key=mock_api_key)

            project_root = tmp_path / "novel-factory"
            chapters_dir = project_root / "03_内容仓库" / "04_正文"
            chapters_dir.mkdir(parents=True)

            # Use a non-standard chapter number to avoid finding real content
            ch_file = chapters_dir / "ch999.md"
            ch_file.write_text("测试章节正文内容", encoding='utf-8')

            checker.project_root = project_root

            content = checker.read_chapter(999)
            assert content is not None
            assert "测试章节正文内容" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])