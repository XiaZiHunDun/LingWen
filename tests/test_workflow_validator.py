"""workflow_validator 单元测试"""

import pytest

from infra.state.workflow_validator import (
    ALL_STEPS,
    VALID_TRANSITIONS,
    get_allowed_transitions,
    is_valid_step,
    validate_transition,
)


class TestValidateTransition:
    """validate_transition 函数测试"""

    # 合法转换测试
    def test_normal_forward_transition(self):
        """正常前进转换"""
        assert validate_transition('STEP_14', 'STEP_15') == (True, "")
        assert validate_transition('STEP_15', 'STEP_16') == (True, "")
        assert validate_transition('STEP_17', 'STEP_18') == (True, "")

    def test_re_review_transition(self):
        """重审转换（STEP_16 → STEP_16）"""
        is_valid, msg = validate_transition('STEP_16', 'STEP_16')
        assert is_valid is True
        assert msg == ""

    def test_rejection_transition(self):
        """退回重写转换"""
        # STEP_18 可退回到 STEP_16
        is_valid, msg = validate_transition('STEP_18', 'STEP_16')
        assert is_valid is True
        assert msg == ""

    def test_phase_complete_transition(self):
        """完成阶段转换"""
        is_valid, msg = validate_transition('STEP_21', 'PHASE_COMPLETE')
        assert is_valid is True
        assert msg == ""

    # 非法转换测试
    def test_skip_step_forbidden(self):
        """跳过步骤被禁止"""
        # STEP_14 不能直接跳到 STEP_16
        is_valid, msg = validate_transition('STEP_14', 'STEP_16')
        assert is_valid is False
        assert "非法状态转换" in msg

    def test_backward_transition_forbidden(self):
        """倒退转换被禁止"""
        is_valid, msg = validate_transition('STEP_21', 'STEP_19')
        assert is_valid is False
        assert "非法状态转换" in msg

    def test_invalid_step_forbidden(self):
        """无效步骤转换被禁止"""
        is_valid, msg = validate_transition('STEP_99', 'STEP_01')
        assert is_valid is False

    def test_skip_multiple_steps_forbidden(self):
        """跳过多个步骤被禁止"""
        # STEP_12 不能跳到 STEP_14
        is_valid, msg = validate_transition('STEP_12', 'STEP_14')
        assert is_valid is False
        assert "非法状态转换" in msg


class TestGetAllowedTransitions:
    """get_allowed_transitions 函数测试"""

    def test_returns_list_of_allowed(self):
        """返回允许的转换列表"""
        allowed = get_allowed_transitions('STEP_16')
        assert 'STEP_17' in allowed
        assert 'STEP_16' in allowed  # 重审

    def test_unknown_step_returns_empty(self):
        """未知步骤返回空列表"""
        allowed = get_allowed_transitions('STEP_99')
        assert allowed == []


class TestIsValidStep:
    """is_valid_step 函数测试"""

    def test_valid_step_returns_true(self):
        """有效步骤返回True"""
        assert is_valid_step('STEP_12') is True
        assert is_valid_step('STEP_16') is True
        assert is_valid_step('STEP_21') is True

    def test_invalid_step_returns_false(self):
        """无效步骤返回False"""
        assert is_valid_step('STEP_99') is False
        assert is_valid_step('INVALID') is False
        assert is_valid_step('') is False

    def test_phase_complete_is_valid(self):
        """PHASE_COMPLETE 是有效终点"""
        assert is_valid_step('PHASE_COMPLETE') is True


class TestWorkflowIntegrity:
    """工作流完整性测试"""

    def test_all_steps_have_at_least_one_transition(self):
        """所有步骤都有至少一个转换目标"""
        for step in ALL_STEPS:
            # PHASE_* 标记是阶段入口，不是可转换的步骤，跳过
            if step.startswith('PHASE_'):
                continue
            allowed = get_allowed_transitions(step)
            assert len(allowed) > 0, f"{step} 没有允许的转换"

    def test_all_transitions_are_valid_steps(self):
        """所有转换目标都是有效步骤"""
        for current_step, targets in VALID_TRANSITIONS.items():
            for target in targets:
                # 目标要么是有效的STEP，要么是PHASE_COMPLETE
                is_step = target.startswith('STEP_') or target == 'PHASE_COMPLETE'
                is_phase_marker = target.startswith('PHASE_')
                assert is_step or is_phase_marker, \
                    f"{current_step} → {target}: 目标不是有效步骤"

    def test_no_step_can_go_to_itself_except_re_review(self):
        """除重审外，步骤不能转换到自身"""
        for step, targets in VALID_TRANSITIONS.items():
            if step in ['STEP_16']:  # STEP_16 允许重审
                continue
            if step.startswith('STEP_'):
                assert step not in targets, \
                    f"{step} 不应该能转换到自身"


class TestBoundaryConditions:
    """边界条件测试"""

    def test_empty_current_step(self):
        """空字符串作为当前步骤"""
        is_valid, msg = validate_transition('', 'STEP_01')
        assert is_valid is False

    def test_empty_target_step(self):
        """空字符串作为目标步骤"""
        is_valid, msg = validate_transition('STEP_01', '')
        assert is_valid is False

    def test_none_current_step(self):
        """None 作为当前步骤"""
        is_valid, msg = validate_transition(None, 'STEP_01')
        assert is_valid is False

    def test_none_target_step(self):
        """None 作为目标步骤"""
        is_valid, msg = validate_transition('STEP_01', None)
        assert is_valid is False
