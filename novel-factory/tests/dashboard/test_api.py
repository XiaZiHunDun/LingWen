"""
Tests for the Reading Power Dashboard API.
"""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard.app import ReadingPowerDB, create_app


class TestHealthEndpoint:
    """Tests for the /api/health endpoint."""

    def test_health_returns_healthy_status(self):
        """Health endpoint should return healthy status."""
        app = create_app(db_path=Path(tempfile.mktemp()))
        client = TestClient(app)
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "reading-power-dashboard"


class TestOverviewEndpoint:
    """Tests for the /api/overview endpoint."""

    def test_overview_returns_zeros_when_db_not_found(self):
        """Overview should return empty data when DB doesn't exist."""
        app = create_app(db_path=Path("/nonexistent/path/reading_power.db"))
        client = TestClient(app)
        response = client.get("/api/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["total_chapters"] == 0
        assert data["total_hooks"] == 0
        assert data["avg_hook_strength"] == 0.0
        assert data["total_coolpoints"] == 0
        assert data["avg_coolpoint_density"] == 0.0

    def test_overview_returns_zeros_when_db_empty(self):
        """Overview should return empty data when database has no data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            # Create empty database
            ReadingPowerDB(db_path)
            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/overview")

            assert response.status_code == 200
            data = response.json()
            assert data["total_chapters"] == 0
            assert data["total_hooks"] == 0
            assert data["avg_hook_strength"] == 0.0
            assert data["total_coolpoints"] == 0
            assert data["avg_coolpoint_density"] == 0.0
        finally:
            db_path.unlink(missing_ok=True)

    def test_overview_returns_correct_stats(self):
        """Overview should return correct aggregated statistics."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            # Create database with test data
            db = ReadingPowerDB(db_path)

            # Insert test chapter summaries
            db.update_chapter_summary("1", hook_count=3, hook_strength_avg=0.8, coolpoint_count=2, coolpoint_density=0.5)
            db.update_chapter_summary("2", hook_count=5, hook_strength_avg=0.6, coolpoint_count=3, coolpoint_density=0.7)
            db.update_chapter_summary("3", hook_count=2, hook_strength_avg=0.9, coolpoint_count=1, coolpoint_density=0.4)

            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/overview")

            assert response.status_code == 200
            data = response.json()
            assert data["total_chapters"] == 3
            assert data["total_hooks"] == 10  # 3+5+2
            assert abs(data["avg_hook_strength"] - 0.7667) < 0.01  # (0.8+0.6+0.9)/3
            assert data["total_coolpoints"] == 6  # 2+3+1
            assert abs(data["avg_coolpoint_density"] - 0.5333) < 0.01  # (0.5+0.7+0.4)/3
        finally:
            db_path.unlink(missing_ok=True)


class TestChaptersEndpoint:
    """Tests for the /api/chapters endpoint."""

    def test_chapters_returns_empty_when_db_not_found(self):
        """Chapters should return empty array when database doesn't exist."""
        app = create_app(db_path=Path("/nonexistent/path/reading_power.db"))
        client = TestClient(app)
        response = client.get("/api/chapters")

        assert response.status_code == 200
        data = response.json()
        assert data["chapters"] == []

    def test_chapters_returns_empty_when_db_empty(self):
        """Chapters should return empty array when database has no data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            ReadingPowerDB(db_path)
            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/chapters")

            assert response.status_code == 200
            data = response.json()
            assert data["chapters"] == []
        finally:
            db_path.unlink(missing_ok=True)

    def test_chapters_returns_data_for_range(self):
        """Chapters should return data for specified range."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)

            # Insert test chapter summaries
            db.update_chapter_summary("1", hook_count=3, hook_strength_avg=0.8, coolpoint_count=2, coolpoint_density=0.5)
            db.update_chapter_summary("2", hook_count=5, hook_strength_avg=0.6, coolpoint_count=3, coolpoint_density=0.7)
            db.update_chapter_summary("3", hook_count=2, hook_strength_avg=0.9, coolpoint_count=1, coolpoint_density=0.4)

            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/chapters?range=1-3")

            assert response.status_code == 200
            data = response.json()
            chapters = data["chapters"]
            assert len(chapters) == 3

            # Verify first chapter
            assert chapters[0]["chapter"] == 1
            assert chapters[0]["hook_count"] == 3
            assert chapters[0]["hook_strength_avg"] == 0.8
            assert chapters[0]["coolpoint_count"] == 2
            assert chapters[0]["coolpoint_density"] == 0.5
        finally:
            db_path.unlink(missing_ok=True)

    def test_chapters_returns_subset_for_range(self):
        """Chapters should return only chapters within range."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)

            # Insert test chapter summaries
            db.update_chapter_summary("1", hook_count=3, hook_strength_avg=0.8, coolpoint_count=2, coolpoint_density=0.5)
            db.update_chapter_summary("2", hook_count=5, hook_strength_avg=0.6, coolpoint_count=3, coolpoint_density=0.7)
            db.update_chapter_summary("3", hook_count=2, hook_strength_avg=0.9, coolpoint_count=1, coolpoint_density=0.4)

            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/chapters?range=2-3")

            assert response.status_code == 200
            data = response.json()
            chapters = data["chapters"]
            assert len(chapters) == 2
            assert chapters[0]["chapter"] == 2
            assert chapters[1]["chapter"] == 3
        finally:
            db_path.unlink(missing_ok=True)

    def test_chapters_returns_empty_for_out_of_range(self):
        """Chapters should return empty array when no chapters in range."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)

            # Insert only chapter 1
            db.update_chapter_summary("1", hook_count=3, hook_strength_avg=0.8, coolpoint_count=2, coolpoint_density=0.5)

            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/chapters?range=100-200")

            assert response.status_code == 200
            data = response.json()
            assert data["chapters"] == []
        finally:
            db_path.unlink(missing_ok=True)

    def test_chapters_rejects_invalid_range(self):
        """Chapters should reject invalid range format."""
        app = create_app(db_path=Path(tempfile.mktemp()))
        client = TestClient(app)

        # Missing dash
        response = client.get("/api/chapters?range=130")
        assert response.status_code == 400
        assert "Invalid range parameter" in response.json()["detail"]

        # Invalid format
        response = client.get("/api/chapters?range=abc")
        assert response.status_code == 400

        # Start > End
        response = client.get("/api/chapters?range=30-1")
        assert response.status_code == 400
        assert "Invalid range parameter" in response.json()["detail"]

    def test_chapters_uses_default_range(self):
        """Chapters should use default range 1-30 when not specified."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)

            # Insert 35 chapters
            for i in range(1, 36):
                db.update_chapter_summary(
                    str(i),
                    hook_count=i,
                    hook_strength_avg=0.5,
                    coolpoint_count=i,
                    coolpoint_density=0.5,
                )

            app = create_app(db_path=db_path)
            client = TestClient(app)
            response = client.get("/api/chapters")

            assert response.status_code == 200
            data = response.json()
            # Default range is 1-30
            assert len(data["chapters"]) == 30
            assert data["chapters"][0]["chapter"] == 1
            assert data["chapters"][29]["chapter"] == 30
        finally:
            db_path.unlink(missing_ok=True)


class TestReadingPowerDB:
    """Tests for the ReadingPowerDB helper class."""

    def test_exists_returns_false_for_nonexistent_path(self):
        """exists() should return False when database doesn't exist."""
        db = ReadingPowerDB(Path("/nonexistent/path/reading_power.db"), init_if_missing=False)
        assert db.exists() is False

    def test_exists_returns_true_for_existing_db(self):
        """exists() should return True when database file exists."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)
            assert db.exists() is True
        finally:
            db_path.unlink(missing_ok=True)

    def test_is_empty_returns_true_for_nonexistent_db(self):
        """is_empty() should return True when database doesn't exist."""
        db = ReadingPowerDB(Path("/nonexistent/path/reading_power.db"), init_if_missing=False)
        assert db.is_empty() is True

    def test_is_empty_returns_true_for_empty_db(self):
        """is_empty() should return True when database has no chapter summaries."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)
            assert db.is_empty() is True
        finally:
            db_path.unlink(missing_ok=True)

    def test_is_empty_returns_false_for_db_with_data(self):
        """is_empty() should return False when database has chapter summaries."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)
            db.update_chapter_summary("1", 1, 0.5, 1, 0.5)
            assert db.is_empty() is False
        finally:
            db_path.unlink(missing_ok=True)

    def test_get_overview_stats_returns_none_for_nonexistent_db(self):
        """get_overview_stats() should return None when database doesn't exist."""
        db = ReadingPowerDB(Path("/nonexistent/path/reading_power.db"), init_if_missing=False)
        assert db.get_overview_stats() is None

    def test_get_chapters_range_returns_empty_for_nonexistent_db(self):
        """get_chapters_range() should return empty list when database doesn't exist."""
        db = ReadingPowerDB(Path("/nonexistent/path/reading_power.db"), init_if_missing=False)
        assert db.get_chapters_range(1, 30) == []

    def test_get_chapters_range_returns_empty_for_out_of_range(self):
        """get_chapters_range() should return empty list when no chapters in range."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        try:
            db = ReadingPowerDB(db_path)
            db.update_chapter_summary("1", 1, 0.5, 1, 0.5)
            assert db.get_chapters_range(100, 200) == []
        finally:
            db_path.unlink(missing_ok=True)
