"""状态转换校验器 - 三条铁律之一：禁止跳过"""

import logging

from infra.logging_config import logger

# 工作流步骤有效转换映射
# Key: 当前步骤
# Value: 允许转换到的目标步骤列表
VALID_TRANSITIONS = {
    # PHASE_0 初始化
    'STEP_00': ['STEP_01'],
    # PHASE_1 构思期
    'STEP_01': ['STEP_02'],
    'STEP_02': ['STEP_03'],
    'STEP_03': ['STEP_04'],
    'STEP_04': ['PHASE_2_START'],
    # PHASE_2 规划期
    'STEP_05': ['STEP_06'],
    'STEP_06': ['STEP_07'],
    'STEP_07': ['STEP_08'],
    'STEP_08': ['PHASE_3_START'],
    # PHASE_3 验证期
    'STEP_09': ['STEP_10'],
    'STEP_10': ['STEP_11'],
    'STEP_11': ['PHASE_4_START'],
    # PHASE_4 写作期
    'STEP_12': ['STEP_13'],
    'STEP_13': ['STEP_14'],
    # PHASE_5 修改期
    'STEP_14': ['STEP_15'],
    'STEP_15': ['STEP_16'],
    # PHASE_6 审核期
    'STEP_16': ['STEP_17', 'STEP_16'],  # 允许重审（退回到16）
    'STEP_17': ['STEP_18'],
    'STEP_18': ['STEP_19', 'STEP_16'],   # 验证失败可退回重写
    # PHASE_7 完成期
    'STEP_19': ['STEP_20'],
    'STEP_20': ['STEP_21'],
    'STEP_21': ['PHASE_COMPLETE'],
}

# 用于测试的便捷常量
ALL_STEPS = [
    'STEP_00', 'STEP_01', 'STEP_02', 'STEP_03', 'STEP_04',
    'STEP_05', 'STEP_06', 'STEP_07', 'STEP_08',
    'STEP_09', 'STEP_10', 'STEP_11',
    'STEP_12', 'STEP_13', 'STEP_14', 'STEP_15',
    'STEP_16', 'STEP_17', 'STEP_18',
    'STEP_19', 'STEP_20', 'STEP_21',
]


def validate_transition(current_step: str, target_step: str) -> tuple[bool, str]:
    """校验状态转换是否合法

    根据三条铁律之一的"禁止跳过"原则，校验工作流状态转换是否符合预定义的合法路径。

    Args:
        current_step: 当前工作流步骤
        target_step: 目标工作流步骤

    Returns:
        tuple[bool, str]: (是否合法, 错误信息)
            - (True, "") 表示转换合法
            - (False, "非法状态转换: ...") 表示转换非法

    Example:
        >>> validate_transition('STEP_14', 'STEP_15')
        (True, '')
        >>> validate_transition('STEP_14', 'STEP_16')
        (False, '非法状态转换: STEP_14 → STEP_16')
    """
    allowed = VALID_TRANSITIONS.get(current_step, [])
    if target_step in allowed:
        return (True, "")
    logger.warning(f"非法状态转换被拒绝: {current_step} → {target_step}")
    return (False, f"非法状态转换: {current_step} → {target_step}")


def get_allowed_transitions(current_step: str) -> list[str]:
    """获取当前步骤允许的所有转换目标

    Args:
        current_step: 当前工作流步骤

    Returns:
        list[str]: 允许转换到的目标步骤列表
    """
    return VALID_TRANSITIONS.get(current_step, [])


def is_valid_step(step: str) -> bool:
    """检查步骤是否为有效的工作流步骤

    Args:
        step: 待检查的步骤标识

    Returns:
        bool: 是否为有效步骤
    """
    # VALID_TRANSITIONS 的 key 都是有效步骤
    if step in VALID_TRANSITIONS:
        return True
    # PHASE_COMPLETE 是有效的终点
    if step == 'PHASE_COMPLETE':
        return True
    return False


# 模块自测
if __name__ == '__main__':
    print("workflow_validator 自测")
    print("=" * 50)

    # 测试合法转换
    valid_cases = [
        ('STEP_14', 'STEP_15'),
        ('STEP_15', 'STEP_16'),
        ('STEP_16', 'STEP_17'),
        ('STEP_16', 'STEP_16'),  # 重审
        ('STEP_18', 'STEP_19'),
        ('STEP_18', 'STEP_16'),  # 退回重写
        ('STEP_21', 'PHASE_COMPLETE'),
    ]

    print("\n合法转换测试:")
    all_valid = True
    for current, target in valid_cases:
        is_valid, msg = validate_transition(current, target)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {current} → {target}")
        if not is_valid:
            all_valid = False

    # 测试非法转换
    invalid_cases = [
        ('STEP_14', 'STEP_16'),   # 跳过STEP_15
        ('STEP_14', 'STEP_17'),   # 跳过STEP_15/16
        ('STEP_12', 'STEP_14'),   # 跳过STEP_13
        ('STEP_21', 'STEP_19'),   # 倒退
        ('STEP_15', 'STEP_13'),   # 倒退
        ('STEP_99', 'STEP_01'),   # 无效步骤
    ]

    print("\n非法转换测试:")
    all_invalid = True
    for current, target in invalid_cases:
        is_valid, msg = validate_transition(current, target)
        status = "✓" if not is_valid else "✗"
        print(f"  {status} {current} → {target}: {msg}")
        if is_valid:
            all_invalid = False

    print("=" * 50)
    if all_valid and all_invalid:
        print("全部测试通过 ✓")
    else:
        print("存在测试失败 ✗")
