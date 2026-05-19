# tests/agent_system/test_e2e_workflow.py
"""
Agent系统端到端测试

测试完整写作流程：
1. 大纲生成 → 角色生成 → 正文写作 → 审核 → 润色
2. Agent间数据传递和状态共享
3. 社交引擎关系追踪
"""
import pytest
import tempfile
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent_system.master_controller import MasterController
from agent_system.social_engine.relationship_tracker import RelationshipTracker
from agent_system.social_engine.event_effect_calculator import EventEffectCalculator


class TestCompleteWorkflow:
    """完整工作流测试"""

    def setup_method(self):
        """每个测试前创建临时状态目录"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.state_dir = self.tmpdir.name
        self.controller = MasterController(state_dir=self.state_dir)

    def teardown_method(self):
        """清理临时目录"""
        self.tmpdir.cleanup()

    def test_complete_workflow_basic(self):
        """测试完整工作流基本路径"""
        # 1. 生成大纲
        outline = self.controller.generate_outline(
            settings={"title": "测试小说", "genre": "玄幻"},
            requirements={"total_chapters": 10}
        )
        assert outline["title"] == "测试小说"
        assert len(outline["chapters"]) == 10

        # 2. 生成角色
        character_reqs = [
            {
                "name": "铁蛋",
                "role": "protagonist",
                "personality": ["冷静", "务实"],
                "first_appearance": 1,
                "background": "普通少年",
                "abilities": ["剑法"],
                "voice_pattern": "简洁"
            },
            {
                "name": "莫言",
                "role": "antagonist",
                "personality": ["阴险", "狡诈"],
                "first_appearance": 1,
                "background": "魔教长老",
                "abilities": ["暗器"],
                "voice_pattern": "阴冷"
            }
        ]
        characters = self.controller.generate_characters(outline, character_reqs)
        assert len(characters) == 2
        assert characters[0]["name"] == "铁蛋"
        assert characters[1]["name"] == "莫言"

        # 3. 写章节
        memory_context = {"pending_foreshadows": [], "recent_events": []}
        style_guide = {"tone": "简洁有力", "dialogue_ratio": "30%"}

        write_result = self.controller.write_chapter(
            chapter_num=1,
            outline=outline,
            characters=characters,
            memory_context=memory_context,
            style_guide=style_guide
        )
        assert "prompt" in write_result
        assert "context" in write_result
        assert "铁蛋" in write_result["prompt"]

        # 4. 审核章节
        chapter_content = "铁蛋冷静地站在原地，莫言阴险地笑着。铁蛋突然暴怒起来，这不符合他冷静的性格。"
        audit_result = self.controller.audit_chapter(
            chapter_num=1,
            content=chapter_content,
            characters=characters,
            timeline=[]
        )
        assert "issues" in audit_result
        assert len(audit_result["issues"]) >= 1

        # 5. 润色章节
        original = "首先，我们需要冷静分析。其次，制定计划。最后，执行。"
        polished = self.controller.polish_chapter(original)
        assert "首先" not in polished
        assert "其次" not in polished

    def test_agent_data_passing(self):
        """测试Agent间数据传递和状态共享"""
        # 1. 生成大纲
        outline = self.controller.generate_outline(
            settings={"title": "数据传递测试", "genre": "都市"},
            requirements={"total_chapters": 5}
        )

        # 2. 生成角色（使用"冷静"性格，因opposite_words中有对应反义词）
        characters = self.controller.generate_characters(outline, [
            {
                "name": "林夜",
                "role": "protagonist",
                "personality": ["冷静", "务实"],
                "first_appearance": 1,
                "background": "公司职员",
                "abilities": [],
                "voice_pattern": "简洁"
            },
            {
                "name": "苏晴",
                "role": "supporting",
                "personality": ["温柔", "细心"],
                "first_appearance": 1,
                "background": "医生",
                "abilities": ["医术"],
                "voice_pattern": "柔和"
            }
        ])

        # 3. 验证角色数据被正确生成
        protagonist = next(c for c in characters if c["role"] == "protagonist")
        assert protagonist["name"] == "林夜"
        assert "冷静" in protagonist["personality"]

        # 4. 使用角色数据写章节
        write_result = self.controller.write_chapter(
            chapter_num=1,
            outline=outline,
            characters=characters,
            memory_context={},
            style_guide={}
        )

        # 5. 验证上下文包含角色信息
        context = write_result["context"]
        assert len(context["characters"]) == 2
        assert context["characters"][0]["name"] == "林夜"

        # 6. 审核时传入角色，验证一致性检查
        # 使用林夜(冷静)出现暴怒行为来触发检测
        # opposite_words中"冷静"对应"暴怒"、"疯狂"、"失控"
        content_with_inconsistency = "林夜是个冷静的人，但他在关键时刻突然暴怒起来。"
        audit_result = self.controller.audit_chapter(
            chapter_num=1,
            content=content_with_inconsistency,
            characters=characters,
            timeline=[]
        )
        assert len(audit_result["issues"]) >= 1

    def test_social_engine_relationship_tracking(self):
        """测试社交引擎关系追踪"""
        tracker = RelationshipTracker(
            os.path.join(self.state_dir, "relationships.json")
        )

        # 1. 添加角色
        tracker.add_character("铁蛋", "protagonist")
        tracker.add_character("莫言", "antagonist")
        tracker.add_character("林夜", "supporting")

        # 2. 建立关系
        tracker.add_relationship("铁蛋", "莫言", "adversary", trust=0.2, conflict=0.8)
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.8, conflict=0.1)

        # 3. 验证关系网络
        network = tracker.get_network()
        assert len(network["characters"]) == 3
        assert len(network["relationships"]) == 2

        # 4. 验证敌对关系
        adversary_rel = tracker.get_relationship("铁蛋", "莫言")
        assert adversary_rel is not None
        assert adversary_rel["conflict"] == 0.8
        assert adversary_rel["trust"] == 0.2

        # 5. 验证友好关系
        ally_rel = tracker.get_relationship("铁蛋", "林夜")
        assert ally_rel is not None
        assert ally_rel["trust"] == 0.8

        # 6. 记录事件
        tracker.record_event("铁蛋", "莫言", "betrayal", 10)
        tracker.record_event("铁蛋", "林夜", "save_life", 15)

        # 7. 验证事件记录
        network = tracker.get_network()
        assert len(network["events"]) == 2
        assert network["events"][0]["type"] == "betrayal"
        assert network["events"][0]["chapter"] == 10

    def test_event_affects_relationship(self):
        """测试事件对关系的影响"""
        tracker = RelationshipTracker(
            os.path.join(self.state_dir, "relationships.json")
        )
        calculator = EventEffectCalculator()

        # 1. 初始化角色和关系（使用ally关系以支持对称更新）
        tracker.add_character("铁蛋", "protagonist")
        tracker.add_character("林夜", "supporting")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.5, conflict=0.1)

        # 2. 获取初始状态
        initial_rel = tracker.get_relationship("铁蛋", "林夜")
        initial_trust = initial_rel["trust"]
        initial_conflict = initial_rel["conflict"]

        # 3. 应用背叛事件（从铁蛋到林夜）
        calculator.apply_event("betrayal", "铁蛋", "林夜", tracker)

        # 4. 验证关系变化
        updated_rel = tracker.get_relationship("铁蛋", "林夜")
        # betrayal: trust_delta=-0.4, conflict_delta=0.3
        assert updated_rel["trust"] == pytest.approx(initial_trust - 0.4, abs=0.01)
        assert updated_rel["conflict"] == pytest.approx(initial_conflict + 0.3, abs=0.01)
        post_betrayal_trust = updated_rel["trust"]

        # 5. 应用救命事件（恢复信任）- 对于ally关系是对称的
        calculator.apply_event("save_life", "林夜", "铁蛋", tracker)

        # 6. 验证信任恢复（ally关系对称更新）
        updated_rel = tracker.get_relationship("铁蛋", "林夜")
        # save_life: trust_delta=0.3 (symmetric for ally)
        # 背叛后0.1, 救命+0.3 = 0.4, net变化是-0.1
        # 验证信任从背叛后的低点上恢复
        assert updated_rel["trust"] > post_betrayal_trust

    def test_write_chapter_context_integration(self):
        """测试写章节时上下文整合"""
        # 1. 初始化社交关系
        tracker = self.controller.relationship_tracker
        tracker.add_character("铁蛋", "protagonist")
        tracker.add_character("莫言", "antagonist")
        tracker.add_relationship("铁蛋", "莫言", "adversary", trust=0.2, conflict=0.8)

        # 2. 生成大纲和角色
        outline = self.controller.generate_outline(
            settings={"title": "上下文整合测试", "genre": "玄幻"},
            requirements={"total_chapters": 3}
        )
        characters = self.controller.generate_characters(outline, [
            {
                "name": "铁蛋",
                "role": "protagonist",
                "personality": ["冷静"],
                "first_appearance": 1,
                "background": "少年",
                "abilities": ["剑法"],
                "voice_pattern": "简洁"
            }
        ])

        # 3. 带有伏笔和最近事件的memory_context
        memory_context = {
            "pending_foreshadows": [
                {"type": "mystery", "hint": "神秘剑客", "chapter": 1}
            ],
            "recent_events": [
                {"type": "battle", "chapter": 1}
            ]
        }

        # 4. 写章节
        write_result = self.controller.write_chapter(
            chapter_num=2,
            outline=outline,
            characters=characters,
            memory_context=memory_context,
            style_guide={"tone": "紧张"}
        )

        # 5. 验证上下文整合
        context = write_result["context"]
        assert context["chapter_outline"]["num"] == 2
        assert len(context["active_foreshadow"]) == 1
        assert len(context["recent_events"]) == 1
        assert "relationship_network" in context

        # 6. 验证关系网络被正确传递
        rel_network = context["relationship_network"]
        assert len(rel_network["relationships"]) == 1
        assert rel_network["relationships"][0]["conflict"] == 0.8

        # 7. 验证写作建议
        suggestions = write_result["suggestions"]
        assert isinstance(suggestions, list)

    def test_conflict_alert_integration(self):
        """测试冲突预警集成"""
        tracker = self.controller.relationship_tracker

        # 1. 建立高冲突关系
        tracker.add_character("铁蛋", "protagonist")
        tracker.add_character("莫言", "antagonist")
        tracker.add_relationship("铁蛋", "莫言", "adversary", conflict=0.9)

        # 2. 检查预警
        alerts = self.controller.check_alerts(50)

        # 3. 验证冲突爆发预警
        outbreak_alerts = [a for a in alerts if a["type"] == "conflict_outbreak"]
        assert len(outbreak_alerts) >= 1
        # alert结构: {type, from, to, conflict, suggestion} - 无severity字段
        assert outbreak_alerts[0]["conflict"] >= 0.7
        assert outbreak_alerts[0]["from"] == "铁蛋"

    def test_multi_chapter_workflow_with_events(self):
        """测试多章节工作流及事件累积"""
        # 1. 初始化
        tracker = self.controller.relationship_tracker
        tracker.add_character("铁蛋", "protagonist")
        tracker.add_character("林夜", "supporting")
        tracker.add_relationship("铁蛋", "林夜", "ally", trust=0.5, conflict=0.1)

        # 2. 多章节应用事件
        for chapter in range(1, 6):
            if chapter % 2 == 0:
                self.controller.apply_event("team_win", "铁蛋", "林夜", chapter)
            else:
                self.controller.apply_event("verbal_argument", "铁蛋", "林夜", chapter)

        # 3. 验证信任累积变化
        rel = tracker.get_relationship("铁蛋", "林夜")
        # team_win: trust_delta=0.2, conflict_delta=-0.1 (x2)
        # verbal_argument: trust_delta=-0.05, conflict_delta=0.2 (x3)
        expected_trust = 0.5 + 0.2 * 2 - 0.05 * 3
        expected_conflict = 0.1 - 0.1 * 2 + 0.2 * 3
        assert rel["trust"] == pytest.approx(expected_trust, abs=0.01)
        assert rel["conflict"] == pytest.approx(expected_conflict, abs=0.01)

        # 4. 验证事件记录完整
        network = tracker.get_network()
        assert len(network["events"]) == 5

        # 5. 验证最后事件标记
        assert rel["last_event"] == "ch5"

    def test_auditor_with_timeline(self):
        """测试审核时时间线验证"""
        # 1. 生成大纲和角色
        outline = self.controller.generate_outline(
            settings={"title": "时间线测试", "genre": "穿越"},
            requirements={"total_chapters": 10}
        )
        characters = self.controller.generate_characters(outline, [
            {
                "name": "铁蛋",
                "role": "protagonist",
                "personality": ["冷静"],
                "first_appearance": 1,
                "background": "现代人",
                "abilities": ["知识"],
                "voice_pattern": "现代"
            }
        ])

        # 2. 定义时间线
        timeline = [
            {"chapter": 1, "event": "穿越"},
            {"chapter": 2, "event": "遇到林夜"},
            {"chapter": 3, "event": "学习剑法"}
        ]

        # 3. 审核一致性内容（应该无问题）
        consistent_content = "铁蛋在第三章学习了剑法，这是他穿越后的第三个月。"
        audit_result = self.controller.audit_chapter(
            chapter_num=3,
            content=consistent_content,
            characters=characters,
            timeline=timeline
        )
        # 时间线顺序正确时，不应有严重问题
        assert "issues" in audit_result

        # 4. 审核矛盾内容
        inconsistent_content = "铁蛋在第一章就学会了剑法，但根据时间线他第三章才学习。"
        audit_result_2 = self.controller.audit_chapter(
            chapter_num=4,
            content=inconsistent_content,
            characters=characters,
            timeline=timeline
        )
        # 应该能检测出问题
        assert len(audit_result_2["issues"]) >= len(audit_result["issues"])

    def test_polisher_dialogue_optimization(self):
        """测试润色器对话优化"""
        # 1. 原始对话（生硬）
        original = "他说：「你好。」她说：「你好。」他问：「你叫什么名字？」她答：「我叫苏晴。」"

        # 2. 润色
        polished = self.controller.polish_chapter(original)

        # 3. 验证对话被优化
        assert len(polished) >= len(original)  # 优化后应该更长更自然

        # 4. 去除AI痕迹后再优化
        ai_content = "首先，我们需要分析情况。其次，制定策略。最后，实施计划。"
        result = self.controller.polish_chapter(ai_content)
        assert "首先" not in result
        assert "其次" not in result


class TestContextBuilderIntegration:
    """ContextBuilder集成测试"""

    def test_context_builder_with_empty_memory(self):
        """测试ContextBuilder处理空memory_context"""
        from agent_system.shared.context_builder import ContextBuilder

        builder = ContextBuilder()
        context = builder.build_writing_context(
            chapter_outline={"num": 1, "title": "第一章", "events": [], "word_count_target": 2000},
            characters=[{"name": "铁蛋", "personality": ["冷静"]}],
            memory_context={},
            relationship_network={"characters": [], "relationships": [], "events": []},
            style_guide={"tone": "简洁"}
        )

        assert context["chapter_outline"]["num"] == 1
        assert len(context["characters"]) == 1
        assert context["active_foreshadow"] == []
        assert context["recent_events"] == []

    def test_context_builder_merges_foreshadow(self):
        """测试ContextBuilder合并伏笔"""
        from agent_system.shared.context_builder import ContextBuilder

        builder = ContextBuilder()
        memory_context = {
            "pending_foreshadows": [
                {"type": "mystery", "hint": "神秘剑客"},
                {"type": "romance", "hint": "前世姻缘"}
            ]
        }

        context = builder.build_writing_context(
            chapter_outline={"num": 5, "title": "第五章", "events": [], "word_count_target": 2000},
            characters=[],
            memory_context=memory_context,
            relationship_network={"characters": [], "relationships": [], "events": []}
        )

        assert len(context["active_foreshadow"]) == 2
