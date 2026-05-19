"""CharacterTracker 测试"""
import pytest
from pathlib import Path
from unittest.mock import patch

from memory_system.state.character_tracker import CharacterTracker


class TestCharacterTracker:
    """CharacterTracker 测试套件"""

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
        """创建 CharacterTracker 实例"""
        return CharacterTracker(mock_config)

    def test_update_character_state_new_character(self, tracker):
        """测试为新角色更新状态"""
        state = {
            "current_location": "王宫",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 1,
            "emotion_state": "平静",
        }
        tracker.update_character_state("李逍遥", state)

        result = tracker.get_character_state("李逍遥")
        assert result is not None
        assert result["current_location"] == "王宫"
        assert result["current_form"] == "人形"
        assert result["alive"] is True
        assert result["last_updated_chapter"] == 1
        assert result["emotion_state"] == "平静"

    def test_update_character_state_existing_character(self, tracker):
        """测试更新已存在角色的状态"""
        initial_state = {
            "current_location": "王宫",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 1,
            "emotion_state": "平静",
        }
        tracker.update_character_state("李逍遥", initial_state)

        updated_state = {
            "current_location": "客栈",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 5,
            "emotion_state": "紧张",
        }
        tracker.update_character_state("李逍遥", updated_state)

        result = tracker.get_character_state("李逍遥")
        assert result["current_location"] == "客栈"
        assert result["last_updated_chapter"] == 5
        assert result["emotion_state"] == "紧张"

    def test_get_character_state_nonexistent(self, tracker):
        """测试获取不存在的角色状态"""
        result = tracker.get_character_state("不存在的角色")
        assert result is None

    def test_get_all_characters(self, tracker):
        """测试获取所有角色"""
        state1 = {
            "current_location": "王宫",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 1,
            "emotion_state": "平静",
        }
        state2 = {
            "current_location": "山洞",
            "current_form": "狐形",
            "alive": True,
            "last_updated_chapter": 3,
            "emotion_state": "警觉",
        }
        tracker.update_character_state("李逍遥", state1)
        tracker.update_character_state("赵灵儿", state2)

        characters = tracker.get_all_characters()
        assert len(characters) == 2
        assert "李逍遥" in characters
        assert "赵灵儿" in characters

    def test_get_all_characters_empty(self, tracker):
        """测试在没有角色时返回空字典"""
        characters = tracker.get_all_characters()
        assert characters == {}

    def test_character_persistence_after_save_load(self, mock_config, temp_state_dir):
        """测试角色数据在保存和加载后保持一致"""
        tracker1 = CharacterTracker(mock_config)
        state = {
            "current_location": "王宫",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 10,
            "emotion_state": "悲伤",
        }
        tracker1.update_character_state("林青儿", state)

        # 创建新实例模拟重启
        tracker2 = CharacterTracker(mock_config)
        result = tracker2.get_character_state("林青儿")

        assert result is not None
        assert result["current_location"] == "王宫"
        assert result["current_form"] == "人形"
        assert result["alive"] is True
        assert result["last_updated_chapter"] == 10
        assert result["emotion_state"] == "悲伤"

    def test_update_character_with_first_appearance_chapter(self, tracker):
        """测试角色首次出现章节被正确记录"""
        state = {
            "current_location": "仙灵岛",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 1,
            "emotion_state": "好奇",
        }
        tracker.update_character_state("阿奴", state)

        result = tracker.get_character_state("阿奴")
        assert result is not None
        assert result["last_updated_chapter"] == 1

    def test_update_partial_character_state(self, tracker):
        """测试部分更新角色状态（只更新部分字段）"""
        initial_state = {
            "current_location": "王宫",
            "current_form": "人形",
            "alive": True,
            "last_updated_chapter": 1,
            "emotion_state": "平静",
        }
        tracker.update_character_state("酒剑仙", initial_state)

        # 只更新位置和情绪
        partial_update = {
            "current_location": "华山",
            "emotion_state": "醉酒",
        }
        tracker.update_character_state("酒剑仙", partial_update)

        result = tracker.get_character_state("酒剑仙")
        assert result["current_location"] == "华山"
        assert result["emotion_state"] == "醉酒"
        # 其他字段保持不变
        assert result["current_form"] == "人形"
        assert result["alive"] is True