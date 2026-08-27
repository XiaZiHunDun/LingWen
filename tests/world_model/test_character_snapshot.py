"""人物状态快照测试"""

import pytest

from infra.world_model.character_snapshot import (
    CharacterAttributeChange,
    CharacterSnapshot,
    CharacterSnapshotError,
    CharacterState,
    capture_character_state,
    get_character_changes,
)


class TestCharacterState:
    """CharacterState 数据类测试"""

    def test_create_state(self):
        state = CharacterState(
            id="char_001",
            name="张三",
            chapter=3,
            attributes={"age": 25, "mood": "平静"},
        )
        assert state.id == "char_001"
        assert state.name == "张三"
        assert state.chapter == 3
        assert state.attributes == {"age": 25, "mood": "平静"}
        assert state.relationships == {}

    def test_empty_id_raises(self):
        with pytest.raises(Exception):
            CharacterState(id="", name="张三", chapter=1)

    def test_empty_name_raises(self):
        with pytest.raises(Exception):
            CharacterState(id="c1", name="", chapter=1)

    def test_invalid_chapter_raises(self):
        with pytest.raises(Exception):
            CharacterState(id="c1", name="张三", chapter=0)
        with pytest.raises(Exception):
            CharacterState(id="c1", name="张三", chapter=-1)

    def test_to_dict(self):
        state = CharacterState(
            id="c1",
            name="张三",
            chapter=3,
            attributes={"age": 25},
            relationships={"李四": "朋友"},
        )
        d = state.to_dict()
        assert d["id"] == "c1"
        assert d["name"] == "张三"
        assert d["chapter"] == 3
        assert d["attributes"] == {"age": 25}
        assert d["relationships"] == {"李四": "朋友"}

    def test_from_dict(self):
        d = {
            "id": "c1",
            "name": "张三",
            "chapter": 3,
            "attributes": {"age": 25},
            "relationships": {"李四": "朋友"},
        }
        state = CharacterState.from_dict(d)
        assert state.id == "c1"
        assert state.name == "张三"
        assert state.attributes == {"age": 25}


class TestCharacterAttributeChange:
    """CharacterAttributeChange 数据类测试"""

    def test_create_change(self):
        change = CharacterAttributeChange(
            attribute="mood",
            old_value="平静",
            new_value="愤怒",
            chapter=5,
        )
        assert change.attribute == "mood"
        assert change.old_value == "平静"
        assert change.new_value == "愤怒"
        assert change.chapter == 5

    def test_to_dict(self):
        change = CharacterAttributeChange(
            attribute="mood",
            old_value="平静",
            new_value="愤怒",
            chapter=5,
        )
        d = change.to_dict()
        assert d["attribute"] == "mood"
        assert d["old_value"] == "平静"
        assert d["new_value"] == "愤怒"
        assert d["chapter"] == 5


class TestCharacterSnapshot:
    """CharacterSnapshot 核心类测试"""

    def test_empty_chapter_range_raises(self):
        with pytest.raises(CharacterSnapshotError):
            CharacterSnapshot(chapter_range=[], character_states=[])

    def test_basic_snapshot(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        assert snapshot.min_chapter == 1
        assert snapshot.max_chapter == 4
        assert snapshot.character_ids == ("c1",)

    def test_get_state_exact_match(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        state = snapshot.get_state("c1", 3)
        assert state is not None
        assert state.attributes["mood"] == "愤怒"

    def test_get_state_returns_latest_before(self):
        """查询中间章节时返回最近的前一个状态"""
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        state = snapshot.get_state("c1", 2)
        assert state is not None
        assert state.chapter == 1
        assert state.attributes["mood"] == "平静"

    def test_get_state_unknown_character(self):
        snapshot = CharacterSnapshot(range(1, 5), [])
        assert snapshot.get_state("unknown", 1) is None

    def test_get_latest_state(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        latest = snapshot.get_latest_state("c1")
        assert latest is not None
        assert latest.chapter == 3
        assert latest.attributes["mood"] == "愤怒"

    def test_get_latest_state_unknown(self):
        snapshot = CharacterSnapshot(range(1, 5), [])
        assert snapshot.get_latest_state("unknown") is None

    def test_get_changes_for(self):
        """检测属性变更"""
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静", "age": 25}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒", "age": 25}),
            CharacterState(id="c1", name="张三", chapter=5, attributes={"mood": "愤怒", "age": 26}),
        ]
        snapshot = CharacterSnapshot(range(1, 6), states)
        changes = snapshot.get_changes_for("c1")
        assert len(changes) == 2

        # 第一章→第三章: mood 变化
        mood_change = [c for c in changes if c.attribute == "mood"]
        assert len(mood_change) == 1
        assert mood_change[0].old_value == "平静"
        assert mood_change[0].new_value == "愤怒"
        assert mood_change[0].chapter == 3

        # 第三章→第五章: age 变化
        age_change = [c for c in changes if c.attribute == "age"]
        assert len(age_change) == 1
        assert age_change[0].old_value == 25
        assert age_change[0].new_value == 26
        assert age_change[0].chapter == 5

    def test_no_changes_for_single_state(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
        ]
        snapshot = CharacterSnapshot(range(1, 3), states)
        changes = snapshot.get_changes_for("c1")
        assert len(changes) == 0

    def test_get_changes_for_unknown(self):
        snapshot = CharacterSnapshot(range(1, 3), [])
        changes = snapshot.get_changes_for("unknown")
        assert len(changes) == 0

    def test_get_all_changes_in_chapter(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
            CharacterState(id="c2", name="李四", chapter=1, attributes={"status": "正常"}),
            CharacterState(id="c2", name="李四", chapter=3, attributes={"status": "受伤"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        ch3_changes = snapshot.get_all_changes_in_chapter(3)
        assert "c1" in ch3_changes
        assert "c2" in ch3_changes

    def test_get_all_changes(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        all_changes = snapshot.get_all_changes()
        assert "c1" in all_changes
        assert len(all_changes["c1"]) == 1

    def test_relationship_change_detection(self):
        """检测关系变更"""
        states = [
            CharacterState(id="c1", name="张三", chapter=1, relationships={"c2": "朋友"}),
            CharacterState(id="c1", name="张三", chapter=3, relationships={"c2": "敌人"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        changes = snapshot.get_changes_for("c1")
        assert len(changes) == 1
        assert changes[0].attribute == "relationship:c2"
        assert changes[0].old_value == "朋友"
        assert changes[0].new_value == "敌人"

    def test_get_stats(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
            CharacterState(id="c2", name="李四", chapter=1, attributes={"status": "正常"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        stats = snapshot.get_stats()
        assert stats["total_characters"] == 2
        assert stats["total_state_records"] == 3
        assert stats["total_changes"] == 1  # 只有 c1 有变更
        assert stats["characters_with_changes"] == 1

    def test_multiple_characters(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c2", name="李四", chapter=1, attributes={"status": "正常"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
            CharacterState(id="c2", name="李四", chapter=3, attributes={"status": "受伤"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        assert len(snapshot.character_ids) == 2
        assert snapshot.get_changes_for("c1")
        assert snapshot.get_changes_for("c2")

    def test_to_dict_and_from_dict(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = CharacterSnapshot(range(1, 5), states)
        d = snapshot.to_dict()
        restored = CharacterSnapshot.from_dict(d)
        assert restored.character_ids == snapshot.character_ids
        assert restored.get_changes_for("c1") == snapshot.get_changes_for("c1")


class TestModuleLevelFunctions:
    """模块级便捷函数测试"""

    def test_capture_character_state(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
        ]
        snapshot = capture_character_state(range(1, 3), states)
        assert snapshot.character_ids == ("c1",)

    def test_get_character_changes_with_snapshot(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        snapshot = capture_character_state(range(1, 5), states)
        changes = get_character_changes("c1", snapshot=snapshot)
        assert len(changes) == 1

    def test_get_character_changes_without_snapshot(self):
        states = [
            CharacterState(id="c1", name="张三", chapter=1, attributes={"mood": "平静"}),
            CharacterState(id="c1", name="张三", chapter=3, attributes={"mood": "愤怒"}),
        ]
        changes = get_character_changes(
            "c1", character_states=states, chapter_range=range(1, 5)
        )
        assert len(changes) == 1

    def test_get_character_changes_missing_params(self):
        with pytest.raises(CharacterSnapshotError):
            get_character_changes("c1")
