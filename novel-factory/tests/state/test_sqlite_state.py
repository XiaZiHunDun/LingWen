#!/usr/bin/env python3
"""
Tests for SQLite State Manager
"""
import os
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.state.migrate_from_json import migrate_from_json
from infra.state.state_manager import StateManager


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database for testing"""
    db_path = tmp_path / "test_workflow.db"
    sm = StateManager(str(db_path))
    yield sm, db_path


class TestStateManagerBasic:
    """Basic state manager operations"""

    def test_init_creates_schema(self, temp_db):
        """Test that initialization creates correct schema"""
        sm, db_path = temp_db

        conn = sqlite3.connect(str(db_path))
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' ORDER BY name
        """).fetchall()
        conn.close()

        table_names = [t[0] for t in tables]
        assert 'workflow_state' in table_names
        assert 'task' in table_names
        assert 'audit_log' in table_names

    def test_initial_step(self, temp_db):
        """Test initial workflow step is set correctly"""
        sm, db_path = temp_db

        state = sm.get_current_step()
        assert state['current_step'] == 'STEP_00'
        assert 'PHASE' in state['phase']
        assert state['version'] == 'v8.2'

    def test_advance_step_atomic(self, temp_db):
        """Test advancing step is atomic"""
        sm, db_path = temp_db

        result = sm.advance_step('STEP_01', 'PHASE_1_LAUNCH')

        assert result['old']['current_step'] == 'STEP_00'
        assert result['new']['current_step'] == 'STEP_01'
        assert result['new']['phase'] == 'PHASE_1_LAUNCH'

        # Verify persisted
        state = sm.get_current_step()
        assert state['current_step'] == 'STEP_01'

    def test_record_task(self, temp_db):
        """Test recording a new task"""
        sm, db_path = temp_db

        result = sm.record_task('task_001', 'content_writer', 'pending', 'Write ch001')

        assert result['task_id'] == 'task_001'
        assert result['agent'] == 'content_writer'
        assert result['status'] == 'pending'

    def test_update_task_status(self, temp_db):
        """Test updating task status"""
        sm, db_path = temp_db

        sm.record_task('task_001', 'content_writer', 'pending')
        result = sm.record_task('task_001', 'content_writer', 'running')

        assert result['status'] == 'running'

        # Verify in DB
        task = sm.get_task_status('task_001')
        assert task['status'] == 'running'

    def test_get_task_status_not_found(self, temp_db):
        """Test getting non-existent task returns None"""
        sm, db_path = temp_db

        task = sm.get_task_status('nonexistent')
        assert task is None

    def test_get_all_tasks(self, temp_db):
        """Test retrieving all tasks"""
        sm, db_path = temp_db

        sm.record_task('task_001', 'writer_a', 'completed')
        sm.record_task('task_002', 'writer_b', 'pending')

        tasks = sm.get_all_tasks()
        assert len(tasks) == 2

        tasks_pending = sm.get_all_tasks(status='pending')
        assert len(tasks_pending) == 1
        assert tasks_pending[0]['id'] == 'task_002'

    def test_audit_log_records_changes(self, temp_db):
        """Test audit log captures all state changes"""
        sm, db_path = temp_db

        sm.advance_step('STEP_01', 'PHASE_1')
        sm.record_task('task_001', 'writer', 'pending')

        logs = sm.get_audit_log()
        assert len(logs) >= 2

        # Most recent first
        assert logs[0]['action'] == 'create_task'


class TestStateManagerTransaction:
    """Transaction and atomicity tests"""

    def test_transaction_rollback_on_error(self, temp_db):
        """Test that transaction rolls back on error"""
        sm, db_path = temp_db

        initial_state = sm.get_current_step()

        # Try to advance step in a transaction that will fail
        with pytest.raises(Exception):
            with sm._transaction() as conn:
                conn.execute("""
                    UPDATE workflow_state
                    SET current_step = 'STEP_99'
                    WHERE id = 1
                """)
                raise ValueError("Intentional failure for testing")

        # State should be rolled back
        state = sm.get_current_step()
        assert state['current_step'] == initial_state['current_step']


class TestStateManagerConcurrency:
    """Concurrency and flock protection tests"""

    def test_concurrent_updates_serialized(self, temp_db):
        """Test that concurrent updates are properly serialized with flock"""
        sm, db_path = temp_db

        errors = []
        results = []

        def advance_many(step_num):
            try:
                sm.advance_step(f'STEP_{step_num:02d}', 'PHASE_TEST')
                results.append(step_num)
            except Exception as e:
                errors.append(e)

        # Run concurrent advances
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(advance_many, i) for i in range(1, 11)]
            for f in futures:
                f.result()

        # All should succeed (flock serializes them)
        assert len(errors) == 0
        assert len(results) == 10

        # Final state should be the last step
        state = sm.get_current_step()
        assert state['current_step'] == 'STEP_10'

    def test_concurrent_task_writes(self, temp_db):
        """Test concurrent task creation"""
        sm, db_path = temp_db

        def create_tasks(start_id, count):
            for i in range(count):
                sm.record_task(f'concurrent_task_{start_id + i}', 'agent', 'pending')

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(create_tasks, 0, 25),
                executor.submit(create_tasks, 25, 25),
                executor.submit(create_tasks, 50, 25),
                executor.submit(create_tasks, 75, 25),
            ]
            for f in futures:
                f.result()

        tasks = sm.get_all_tasks()
        assert len(tasks) == 100


class TestMigrationFromJson:
    """Test migration from workflow_state.json"""

    def test_migration_creates_backup(self, temp_db, tmp_path):
        """Test that migration creates backup of original"""
        sm, db_path = temp_db

        # Create a minimal JSON file
        json_path = tmp_path / 'workflow_state.json'
        json_data = {
            'version': 'v8.2',
            'current_step': 'STEP_25',
            'current_phase': 'PHASE_7_CLOSE',
            'writer_batches': {
                'batch_001': {
                    'chapter_range': 'ch001-ch010',
                    'status': 'completed',
                    'created_at': '2026-05-20T10:00:00'
                }
            },
            'phases': {
                'PHASE_1': {'name': 'Test'}
            }
        }

        with open(json_path, 'w') as f:
            import json
            json.dump(json_data, f)

        # Run migration
        report = migrate_from_json(json_path, db_path)

        # Check backup created
        assert Path(report['backup_created']).exists()
        assert report['current_step'] == 'STEP_25'
        assert report['tasks_migrated'] >= 1


class TestIntegration:
    """Integration tests with real paths"""

    def test_with_real_project_path(self, tmp_path):
        """Test StateManager with computed project path"""
        # StateManager should work without explicit path
        db_path = tmp_path / '.state' / 'workflow.db'

        # Create state manager
        sm = StateManager(str(db_path))

        # Basic operations
        sm.record_task('test_task', 'test_agent', 'pending')
        task = sm.get_task_status('test_task')

        assert task is not None
        assert task['status'] == 'pending'

        # Advance step
        sm.advance_step('STEP_TEST', 'PHASE_TEST')
        state = sm.get_current_step()

        assert state['current_step'] == 'STEP_TEST'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
