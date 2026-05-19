"""PlotThreadTracker 测试"""
import pytest
from pathlib import Path
from unittest.mock import patch

from memory_system.state.plot_thread_tracker import PlotThreadTracker


class TestPlotThreadTracker:
    """PlotThreadTracker 测试套件"""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """创建临时状态目录"""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        return state_dir

    @pytest.fixture
    def mock_config(self, temp_state_dir):
        """模拟配置"""
        return {
            "storage": {
                "state_file": str(temp_state_dir / "state_tracker.json"),
                "plot_threads_file": str(temp_state_dir / "plot_threads.yaml"),
                "timeline_file": str(temp_state_dir / "timeline.json"),
            }
        }

    @pytest.fixture
    def tracker(self, mock_config):
        """创建 PlotThreadTracker 实例"""
        return PlotThreadTracker(mock_config)

    def test_plant_foreshadow_new(self, tracker):
        """测试登记新伏笔"""
        metadata = {
            "title": "神秘宝剑",
            "description": "在第5章出现的古老宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        result = tracker.get_foreshadow("fp_001")
        assert result is not None
        assert result["title"] == "神秘宝剑"
        assert result["description"] == "在第5章出现的古老宝剑"
        assert result["planted_chapter"] == 5
        assert result["expected_recycle_chapter"] == 50
        assert result["status"] == "pending"

    def test_plant_foreshadow_with_mentions(self, tracker):
        """测试登记伏笔时包含提及章节"""
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "mentions": [5, 12, 25],
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        result = tracker.get_foreshadow("fp_001")
        assert result["mentions"] == [5, 12, 25]

    def test_plant_foreshadow_duplicate(self, tracker):
        """测试重复登记伏笔会更新"""
        metadata1 = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata1)

        metadata2 = {
            "title": "神秘宝剑-更新",
            "planted_chapter": 6,
            "status": "in_progress",
        }
        tracker.plant_foreshadow("fp_001", metadata2)

        result = tracker.get_foreshadow("fp_001")
        assert result["title"] == "神秘宝剑-更新"
        assert result["planted_chapter"] == 6
        assert result["status"] == "in_progress"

    def test_update_foreshadow_status(self, tracker):
        """测试更新伏笔状态"""
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        tracker.update_foreshadow("fp_001", chapter=10, event_type="mention")
        result = tracker.get_foreshadow("fp_001")
        assert 10 in result["mentions"]
        assert result["status"] == "pending"  # mention 不改变状态

    def test_update_foreshadow_status_recycled(self, tracker):
        """测试更新伏笔为已回收状态"""
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        tracker.update_foreshadow("fp_001", chapter=50, event_type="recycle")
        result = tracker.get_foreshadow("fp_001")
        assert result["status"] == "recycled"
        assert result["recycled_chapter"] == 50

    def test_update_foreshadow_status_in_progress(self, tracker):
        """测试更新伏笔为进行中状态"""
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        tracker.update_foreshadow("fp_001", chapter=15, event_type="activate")
        result = tracker.get_foreshadow("fp_001")
        assert result["status"] == "in_progress"

    def test_update_foreshadow_status_invalid(self, tracker):
        """测试更新伏笔为无效状态"""
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        tracker.update_foreshadow("fp_001", chapter=20, event_type="invalidate")
        result = tracker.get_foreshadow("fp_001")
        assert result["status"] == "invalid"

    def test_update_foreshadow_nonexistent(self, tracker):
        """测试更新不存在的伏笔（应该静默处理）"""
        # 不应抛出异常
        tracker.update_foreshadow("fp_999", chapter=10, event_type="mention")
        result = tracker.get_foreshadow("fp_999")
        assert result is None

    def test_get_foreshadow_nonexistent(self, tracker):
        """测试获取不存在的伏笔"""
        result = tracker.get_foreshadow("fp_999")
        assert result is None

    def test_get_all_foreshadows(self, tracker):
        """测试获取所有伏笔"""
        metadata1 = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "status": "pending",
        }
        metadata2 = {
            "title": "失散亲人",
            "planted_chapter": 10,
            "status": "in_progress",
        }
        tracker.plant_foreshadow("fp_001", metadata1)
        tracker.plant_foreshadow("fp_002", metadata2)

        result = tracker.get_all_foreshadows()
        assert len(result) == 2
        assert "fp_001" in result
        assert "fp_002" in result

    def test_get_all_foreshadows_empty(self, tracker):
        """测试在没有伏笔时返回空字典"""
        result = tracker.get_all_foreshadows()
        assert result == {}

    def test_get_pending_foreshadows(self, tracker):
        """测试获取待回收伏笔"""
        metadata1 = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "status": "pending",
        }
        metadata2 = {
            "title": "失散亲人",
            "planted_chapter": 10,
            "expected_recycle_chapter": 80,
            "status": "in_progress",
        }
        metadata3 = {
            "title": "预言实现",
            "planted_chapter": 15,
            "expected_recycle_chapter": 60,
            "status": "recycled",
        }
        tracker.plant_foreshadow("fp_001", metadata1)
        tracker.plant_foreshadow("fp_002", metadata2)
        tracker.plant_foreshadow("fp_003", metadata3)

        result = tracker.get_pending_foreshadows()
        assert len(result) == 2  # fp_001 和 fp_002
        assert "fp_001" in result
        assert "fp_002" in result
        assert "fp_003" not in result

    def test_get_pending_foreshadows_empty(self, tracker):
        """测试没有待回收伏笔时返回空字典"""
        metadata = {
            "title": "已回收伏笔",
            "planted_chapter": 5,
            "status": "recycled",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        result = tracker.get_pending_foreshadows()
        assert result == {}

    def test_foreshadow_persistence_after_save_load(self, mock_config, temp_state_dir):
        """测试伏笔数据在保存和加载后保持一致"""
        tracker1 = PlotThreadTracker(mock_config)
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "expected_recycle_chapter": 50,
            "mentions": [5, 12],
            "status": "in_progress",
        }
        tracker1.plant_foreshadow("fp_001", metadata)

        # 创建新实例模拟重启
        tracker2 = PlotThreadTracker(mock_config)
        result = tracker2.get_foreshadow("fp_001")

        assert result is not None
        assert result["title"] == "神秘宝剑"
        assert result["planted_chapter"] == 5
        assert result["expected_recycle_chapter"] == 50
        assert result["mentions"] == [5, 12]
        assert result["status"] == "in_progress"

    def test_plant_foreshadow_minimal_metadata(self, tracker):
        """测试最少元数据情况下登记伏笔"""
        metadata = {
            "title": "最小伏笔",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        result = tracker.get_foreshadow("fp_001")
        assert result["title"] == "最小伏笔"
        assert result["status"] == "pending"  # 默认状态

    def test_update_foreshadow_adds_chapter_to_mentions(self, tracker):
        """测试更新伏笔时提及章节被添加到列表"""
        metadata = {
            "title": "神秘宝剑",
            "planted_chapter": 5,
            "mentions": [5],
            "status": "pending",
        }
        tracker.plant_foreshadow("fp_001", metadata)

        tracker.update_foreshadow("fp_001", chapter=12, event_type="mention")
        tracker.update_foreshadow("fp_001", chapter=25, event_type="mention")

        result = tracker.get_foreshadow("fp_001")
        assert result["mentions"] == [5, 12, 25]