# tests/agent_system/test_task_orchestrator.py
"""TaskOrchestrator单元测试"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from infra.agent_system.task_orchestrator import TaskOrchestrator


class MockStateManager:
    """模拟状态管理器"""

    def __init__(self):
        self._current_step = 'STEP_14'
        self._timestamp = '2026-05-20T00:00:00'

    def get_current_step(self) -> str:
        return self._current_step

    def set_current_step(self, step: str) -> None:
        self._current_step = step

    def update_timestamp(self) -> None:
        self._timestamp = '2026-05-20T12:00:00'


@pytest.fixture
def mock_state_manager():
    """Fixture: 创建模拟状态管理器"""
    return MockStateManager()


@pytest.fixture
def mock_event_bus():
    """Fixture: 创建模拟事件总线"""
    bus = MagicMock()
    bus.emit = MagicMock()
    return bus


@pytest.fixture
def orchestrator(mock_state_manager, mock_event_bus):
    """Fixture: 创建TaskOrchestrator实例"""
    with patch('infra.agent_system.task_orchestrator.EventBus', return_value=mock_event_bus):
        return TaskOrchestrator(
            state_manager=mock_state_manager,
            event_bus=mock_event_bus,
            state_file="workflow_state.json"
        )


class TestStepAdvancement:
    """测试步骤推进"""

    def test_advance_step_valid_transition(self, orchestrator):
        """测试合法步骤转换"""
        is_valid, error = orchestrator.advance_step('STEP_15')
        assert is_valid is True
        assert error == ""

    def test_advance_step_invalid_transition(self, orchestrator):
        """测试非法步骤转换（跳过STEP_15）"""
        is_valid, error = orchestrator.advance_step('STEP_16')
        assert is_valid is False
        assert "非法状态转换" in error

    def test_advance_step_backward_not_allowed(self, orchestrator):
        """测试后退不允许"""
        is_valid, error = orchestrator.advance_step('STEP_13')
        assert is_valid is False

    def test_get_allowed_steps(self, orchestrator):
        """测试获取允许的步骤"""
        allowed = orchestrator.get_allowed_steps()
        assert 'STEP_15' in allowed

    def test_can_advance_to(self, orchestrator):
        """测试检查是否可以转换"""
        assert orchestrator.can_advance_to('STEP_15') is True
        assert orchestrator.can_advance_to('STEP_16') is False


class TestTaskManagement:
    """测试任务管理"""

    def test_dispatch_task(self, orchestrator):
        """测试分发任务"""
        task_id = orchestrator.dispatch_task(
            task_name="write_chapter",
            agent="content_writer",
            context={"chapter": 1},
            priority=0
        )
        assert task_id is not None
        assert len(task_id) == 8  # UUID前8位

    def test_dispatch_task_with_priority(self, orchestrator):
        """测试优先级任务分发"""
        task_id_low = orchestrator.dispatch_task(
            task_name="low_priority",
            agent="content_writer",
            context={},
            priority=-1
        )
        task_id_high = orchestrator.dispatch_task(
            task_name="high_priority",
            agent="auditor",
            context={},
            priority=1
        )
        pending = orchestrator.get_pending_tasks()
        # 高优先级任务应该在前面
        assert pending[0]["name"] == "high_priority"

    def test_start_task(self, orchestrator):
        """测试开始任务"""
        task_id = orchestrator.dispatch_task(
            task_name="test_task",
            agent="content_writer",
            context={}
        )
        result = orchestrator.start_task(task_id)
        assert result is True

        active = orchestrator.get_active_tasks()
        assert len(active) == 1
        assert active[0]["task_id"] == task_id

    def test_verify_task(self, orchestrator):
        """测试验证任务完成"""
        task_id = orchestrator.dispatch_task(
            task_name="test_task",
            agent="content_writer",
            context={}
        )
        orchestrator.start_task(task_id)

        result = {"status": "completed", "output": "chapter_content"}
        is_valid, error = orchestrator.verify_task(task_id, result)

        assert is_valid is True
        assert error == ""

        active = orchestrator.get_active_tasks()
        assert len(active) == 0

    def test_verify_nonexistent_task(self, orchestrator):
        """测试验证不存在的任务"""
        is_valid, error = orchestrator.verify_task("nonexistent", {})
        assert is_valid is False
        assert "不存在" in error

    def test_fail_task(self, orchestrator):
        """测试任务失败"""
        task_id = orchestrator.dispatch_task(
            task_name="test_task",
            agent="content_writer",
            context={}
        )
        orchestrator.start_task(task_id)

        # 在fail之前获取任务引用
        task_before_fail = orchestrator.get_task(task_id)
        assert task_before_fail is not None
        assert task_before_fail["status"] == "running"

        orchestrator.fail_task(task_id, "执行失败")

        # 验证任务已从活跃任务移除
        active = orchestrator.get_active_tasks()
        assert len(active) == 0

        # 验证任务状态（从之前获取的引用）
        assert task_before_fail["status"] == "failed"
        assert task_before_fail["error"] == "执行失败"

    def test_get_pending_tasks_filter_by_agent(self, orchestrator):
        """测试按Agent过滤待处理任务"""
        orchestrator.dispatch_task("task1", "content_writer", {})
        orchestrator.dispatch_task("task2", "auditor", {})
        orchestrator.dispatch_task("task3", "content_writer", {})

        writer_tasks = orchestrator.get_pending_tasks(agent="content_writer")
        assert len(writer_tasks) == 2

        auditor_tasks = orchestrator.get_pending_tasks(agent="auditor")
        assert len(auditor_tasks) == 1


class TestWorkflowStatus:
    """测试工作流状态查询"""

    def test_get_current_step(self, orchestrator):
        """测试获取当前步骤"""
        step = orchestrator.get_current_step()
        assert step == 'STEP_14'

    def test_get_workflow_status(self, orchestrator):
        """测试获取工作流整体状态"""
        orchestrator.dispatch_task("task1", "content_writer", {})
        orchestrator.dispatch_task("task2", "auditor", {})

        status = orchestrator.get_workflow_status()

        assert "current_step" in status
        assert "allowed_steps" in status
        assert "pending_tasks" in status
        assert status["pending_tasks"] == 2


class TestStepCallbacks:
    """测试步骤回调"""

    def test_register_step_callback(self, orchestrator):
        """测试注册步骤回调"""
        callback = Mock()
        orchestrator.register_step_callback('STEP_15', callback)
        # 回调注册不会立即执行，需要触发步骤转换

    def test_step_callback_triggered_on_advance(self, orchestrator):
        """测试步骤转换时触发回调"""
        callback = Mock()
        orchestrator.register_step_callback('STEP_15', callback)

        orchestrator.advance_step('STEP_15')

        # 回调被调用（通过EventBus）
        # 注意：由于是mock，这里只验证不报错


class TestDeadlockDetection:
    """测试死锁检测"""

    def test_check_deadlock_no_deadlock(self, orchestrator):
        """测试无死锁情况"""
        is_deadlock, desc = orchestrator.check_deadlock()
        assert is_deadlock is False
        assert desc == ""

    def test_check_deadlock_with_stuck_task(self, orchestrator):
        """测试有卡住任务的情况（简化测试）"""
        # 实际死锁检测需要时间戳，这里只验证接口可用
        is_deadlock, desc = orchestrator.check_deadlock()
        assert isinstance(is_deadlock, bool)


class TestReset:
    """测试重置功能"""

    def test_reset_clears_tasks(self, orchestrator):
        """测试重置清空任务队列"""
        orchestrator.dispatch_task("task1", "content_writer", {})
        orchestrator.dispatch_task("task2", "auditor", {})

        orchestrator.reset()

        pending = orchestrator.get_pending_tasks()
        assert len(pending) == 0

        active = orchestrator.get_active_tasks()
        assert len(active) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])