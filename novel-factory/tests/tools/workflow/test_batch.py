"""Tests for infra.tools.workflow.lib.batch (batch_dispatch_writer, batch_dispatch_reviewer).

Batch layer: bulk dispatch of chapter-writing / chapter-review tasks.
"""


class TestBatchDispatch:
    """Tests for batch_dispatch_writer and batch_dispatch_reviewer"""

    def test_batch_dispatch_writer_returns_dict(self, init_db):
        """Test batch_dispatch_writer returns a dictionary"""
        from infra.tools.workflow.lib import batch_dispatch_writer

        result = batch_dispatch_writer(["ch001", "ch002"])

        assert isinstance(result, dict)
        assert "ch001" in result
        assert "ch002" in result

    def test_batch_dispatch_writer_creates_tasks(self, init_db):
        """Test batch_dispatch_writer creates tasks for each chapter"""
        from infra.tools.workflow.lib import batch_dispatch_writer, list_tasks

        batch_dispatch_writer(["ch_batch_1", "ch_batch_2"])

        tasks = list_tasks()
        task_names = [t['task_name'] for t in tasks]
        assert any("ch_batch_1" in name for name in task_names)
        assert any("ch_batch_2" in name for name in task_names)

    def test_batch_dispatch_writer_with_custom_writers(self, init_db):
        """Test batch_dispatch_writer with custom writer list"""
        from infra.tools.workflow.lib import batch_dispatch_writer

        result = batch_dispatch_writer(["chX"], writers=["writer-z"])

        assert "chX" in result

    def test_batch_dispatch_reviewer_returns_dict(self, init_db):
        """Test batch_dispatch_reviewer returns a dictionary"""
        from infra.tools.workflow.lib import batch_dispatch_reviewer

        result = batch_dispatch_reviewer(["ch003"])

        assert isinstance(result, dict)
        assert "ch003" in result

    def test_batch_dispatch_reviewer_creates_review_tasks(self, init_db):
        """Test batch_dispatch_reviewer creates review tasks"""
        from infra.tools.workflow.lib import batch_dispatch_reviewer, list_tasks

        batch_dispatch_reviewer(["ch_review"])

        tasks = list_tasks()
        task_names = [t['task_name'] for t in tasks]
        assert any("ch_review" in name for name in task_names)
