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
    """修复方法签名测试"""

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

    def test_check_character_consistency_exists(self, checker):
        """测试check_character_consistency方法存在"""
        assert hasattr(checker, 'check_character_consistency')
        assert callable(checker.check_character_consistency)

    def test_scan_logic_contradictions_exists(self, checker):
        """测试scan_logic_contradictions方法存在"""
        assert hasattr(checker, 'scan_logic_contradictions')
        assert callable(checker.scan_logic_contradictions)

    def test_verify_foreshadow_completeness_exists(self, checker):
        """测试verify_foreshadow_completeness方法存在"""
        assert hasattr(checker, 'verify_foreshadow_completeness')
        assert callable(checker.verify_foreshadow_completeness)


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
            # 直接设置chapters_dir，因为ComprehensiveQualityChecker使用固定的PROJECT_ROOT
            checker.chapters_dir = chapters_dir

            content = checker.read_chapter(999)
            assert content is not None
            assert "测试章节正文内容" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])