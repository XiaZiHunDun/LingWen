"""物品连续性检查器测试"""

from lingwen_quality.consistency.checkers.item_checker import ItemChecker, ItemState


class TestItemState:
    """ItemState 数据类测试"""

    def test_create_default(self):
        state = ItemState(
            name="木勺",
            owner="张三",
            location="背包",
            condition="良好",
        )
        assert state.name == "木勺"
        assert state.owner == "张三"
        assert state.location == "背包"
        assert state.condition == "良好"
        assert state.quantity == 1

    def test_create_with_quantity(self):
        state = ItemState(
            name="丹药",
            owner="张三",
            location="背包",
            condition="良好",
            quantity=5,
        )
        assert state.quantity == 5


class TestItemChecker:
    """ItemChecker 测试"""

    def test_init(self):
        checker = ItemChecker()
        assert checker._item_history == {}

    def test_init_with_rules(self):
        rules = {"max_items": 10}
        checker = ItemChecker(rules=rules)
        assert checker.rules == rules

    def test_check_empty(self):
        checker = ItemChecker()
        issues = checker.check("", 1, {})
        assert issues == []

    def test_check_no_item_history(self):
        checker = ItemChecker()
        issues = checker.check("章节内容，木勺出现。", 1, {})
        assert issues == []

    def test_check_state_conflict_destroyed(self):
        """已销毁物品再次出现"""
        checker = ItemChecker()
        item_history = {
            "木勺": [ItemState(name="木勺", owner="张三", location="背包",
                                condition="已销毁", quantity=0)],
        }
        context = {"item_history": item_history, "mentioned_items": ["木勺"]}
        # 内容中木勺"完好无损" — 与已销毁冲突
        issues = checker.check("张三拿出木勺，完好无损地展示。", 5, context)
        assert len(issues) >= 1
        assert any("状态冲突" in i.id for i in issues)

    def test_check_state_conflict_lost(self):
        """已丢失物品再次出现"""
        checker = ItemChecker()
        item_history = {
            "宝剑": [ItemState(name="宝剑", owner="张三", location="未知",
                                condition="已丢失", quantity=1)],
        }
        context = {"item_history": item_history, "mentioned_items": ["宝剑"]}
        issues = checker.check("张三手中拿着宝剑，腰间佩着宝剑。", 3, context)
        assert len(issues) >= 1

    def test_check_quantity_conflict_consumable(self):
        """消耗品数量为0但仍有描述"""
        checker = ItemChecker()
        item_history = {
            "丹药": [ItemState(name="丹药", owner="张三", location="背包",
                                condition="已消耗", quantity=0)],
        }
        context = {"item_history": item_history, "mentioned_items": ["丹药"]}
        issues = checker.check("张三还有3颗丹药。", 5, context)
        assert len(issues) >= 1
        assert any("数量冲突" in i.id for i in issues)

    def test_check_no_conflict_normal_use(self):
        """正常使用不报告问题"""
        checker = ItemChecker()
        item_history = {
            "木勺": [ItemState(name="木勺", owner="张三", location="背包",
                                condition="良好", quantity=1)],
        }
        context = {"item_history": item_history, "mentioned_items": ["木勺"]}
        issues = checker.check("张三使用木勺吃饭。", 2, context)
        assert len(issues) == 0

    def test_update_item_state(self):
        checker = ItemChecker()
        new_state = ItemState(
            name="木勺",
            owner="张三",
            location="背包",
            condition="良好",
        )
        checker.update_item_state("木勺", new_state)
        history = checker.get_item_history("木勺")
        assert len(history) == 1
        assert history[0].name == "木勺"

    def test_update_multiple_states(self):
        checker = ItemChecker()
        checker.update_item_state("木勺", ItemState(
            name="木勺", owner="张三", location="背包", condition="良好"))
        checker.update_item_state("木勺", ItemState(
            name="木勺", owner="李四", location="仓库", condition="损坏"))
        history = checker.get_item_history("木勺")
        assert len(history) == 2
        assert history[0].owner == "张三"
        assert history[1].owner == "李四"

    def test_get_item_history_unknown(self):
        checker = ItemChecker()
        history = checker.get_item_history("未知物品")
        assert history == []

    def test_check_realtime(self):
        checker = ItemChecker()
        issues = checker.check_realtime("任意文本")
        assert issues == []

    def test_check_ownership_no_conflict(self):
        """归属转移但不冲突"""
        checker = ItemChecker()
        item_history = {
            "木勺": [
                ItemState(name="木勺", owner="张三", location="背包", condition="良好"),
                ItemState(name="木勺", owner="李四", location="仓库", condition="良好"),
            ],
        }
        context = {"item_history": item_history, "mentioned_items": ["木勺"]}
        issues = checker.check("李四拿着木勺。", 3, context)
        assert len(issues) == 0  # 没有冲突关键词

    def test_check_quantity_non_consumable_ignored(self):
        """非消耗品不检查数量"""
        checker = ItemChecker()
        item_history = {
            "木勺": [ItemState(name="木勺", owner="张三", location="背包",
                                condition="已消耗", quantity=0)],
        }
        context = {"item_history": item_history, "mentioned_items": ["木勺"]}
        # 木勺不是消耗品关键词，数量为0不触发
        issues = checker.check("张三还有3个木勺。", 5, context)
        assert len(issues) == 0  # 木勺不在消耗品关键词中
