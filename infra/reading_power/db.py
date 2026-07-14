"""
Reading Power Database Module for 追读力系统.
Provides SQLite-based storage for hooks, coolpoints, and chapter analysis results.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReadingPowerDB:
    """Database handler for the reading power (追读力) system."""

    DB_PATH = Path(__file__).parent.parent.parent / ".state" / "reading_power.db"

    def __init__(self, db_path=None, init_if_missing: bool = True):
        if isinstance(db_path, str):
            db_path = Path(db_path)
        self.db_path = db_path or self.DB_PATH
        if init_if_missing:
            self._ensure_db_path()
            self._init_db()

    def _ensure_db_path(self) -> None:
        """Ensure the database directory exists."""
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection with Row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database tables and indexes."""
        with self._get_connection() as conn:
            conn.executescript("""
                -- Hooks table: stores reading hooks extracted from chapters
                CREATE TABLE IF NOT EXISTS hooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter TEXT NOT NULL,
                    hook_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    position TEXT NOT NULL,
                    content TEXT NOT NULL,
                    llm_analyzed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chapter, hook_type, position)
                );

                -- Coolpoints table: stores cool point patterns
                CREATE TABLE IF NOT EXISTS coolpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    density REAL NOT NULL,
                    combo_with TEXT,
                    content TEXT NOT NULL,
                    llm_analyzed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chapter, pattern)
                );

                -- Chapter summary table: aggregated reading power metrics per chapter
                CREATE TABLE IF NOT EXISTS chapter_summary (
                    chapter TEXT PRIMARY KEY,
                    hook_count INTEGER DEFAULT 0,
                    hook_strength_avg REAL DEFAULT 0.0,
                    coolpoint_count INTEGER DEFAULT 0,
                    coolpoint_density REAL DEFAULT 0.0,
                    reading_power_score REAL DEFAULT 0.0,
                    last_analyzed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Analysis log table: tracks LLM analysis operations
                CREATE TABLE IF NOT EXISTS analysis_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter TEXT NOT NULL,
                    analyzer_type TEXT NOT NULL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Indexes for efficient lookups
                CREATE INDEX IF NOT EXISTS idx_hooks_chapter ON hooks(chapter);
                CREATE INDEX IF NOT EXISTS idx_coolpoints_chapter ON coolpoints(chapter);
                CREATE INDEX IF NOT EXISTS idx_chapter_summary_chapter ON chapter_summary(chapter);
            """)

    # ==================== Hook CRUD Methods ====================

    def save_hook(
        self,
        chapter: str,
        hook_type: str,
        strength: float,
        position: str,
        content: str,
        llm_analyzed: bool = False,
    ) -> int:
        """
        Save or update a hook for a chapter.

        Args:
            chapter: Chapter identifier
            hook_type: Type of hook (e.g., 'conflict', 'mystery', 'emotion')
            strength: Hook strength score (0.0 - 1.0)
            position: Position in chapter (e.g., 'opening', 'mid', 'cliffhanger')
            content: Hook content text
            llm_analyzed: Whether LLM has analyzed this hook

        Returns:
            Row ID of the inserted/updated hook
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO hooks
                (chapter, hook_type, strength, position, content, llm_analyzed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chapter, hook_type, strength, position, content, int(llm_analyzed), datetime.now().isoformat()),
            )
            return cursor.lastrowid or 0

    def get_hooks(self, chapter: str) -> List[Dict[str, Any]]:
        """
        Retrieve all hooks for a chapter.

        Args:
            chapter: Chapter identifier

        Returns:
            List of hook dictionaries
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM hooks WHERE chapter = ? ORDER BY
                CASE position
                    WHEN 'opening' THEN 1
                    WHEN 'rising' THEN 2
                    WHEN 'mid' THEN 3
                    WHEN 'falling' THEN 4
                    WHEN 'climax' THEN 5
                    WHEN 'ending' THEN 6
                    WHEN 'cliffhanger' THEN 7
                    ELSE 100
                END, id""",
                (chapter,),
            ).fetchall()
            return [dict(row) for row in rows]

    # ==================== Coolpoint CRUD Methods ====================

    def save_coolpoint(
        self,
        chapter: str,
        pattern: str,
        density: float,
        combo_with: Optional[str],
        content: str,
        llm_analyzed: bool = False,
    ) -> int:
        """
        Save or update a coolpoint for a chapter.

        Args:
            chapter: Chapter identifier
            pattern: Coolpoint pattern type (e.g., '觉醒', '反杀', '装逼')
            density: Pattern density score
            combo_with: Combo patterns (comma-separated)
            content: Coolpoint content text
            llm_analyzed: Whether LLM has analyzed this coolpoint

        Returns:
            Row ID of the inserted/updated coolpoint
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO coolpoints
                (chapter, pattern, density, combo_with, content, llm_analyzed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (chapter, pattern, density, combo_with, content, int(llm_analyzed), datetime.now().isoformat()),
            )
            return cursor.lastrowid or 0

    def get_coolpoints(self, chapter: str) -> List[Dict[str, Any]]:
        """
        Retrieve all coolpoints for a chapter.

        Args:
            chapter: Chapter identifier

        Returns:
            List of coolpoint dictionaries
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM coolpoints WHERE chapter = ? ORDER BY density DESC, id",
                (chapter,),
            ).fetchall()
            return [dict(row) for row in rows]

    # ==================== Chapter Summary Methods ====================

    def update_chapter_summary(
        self,
        chapter: str,
        hook_count: int,
        hook_strength_avg: float,
        coolpoint_count: int,
        coolpoint_density: float,
        reading_power_score: Optional[float] = None,
    ) -> None:
        """
        Update or insert chapter summary with aggregated metrics.

        Args:
            chapter: Chapter identifier
            hook_count: Total number of hooks
            hook_strength_avg: Average hook strength
            coolpoint_count: Total number of coolpoints
            coolpoint_density: Average coolpoint density
            reading_power_score: Optional calculated reading power score
        """
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO chapter_summary
                (chapter, hook_count, hook_strength_avg, coolpoint_count, coolpoint_density,
                 reading_power_score, last_analyzed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chapter) DO UPDATE SET
                    hook_count = excluded.hook_count,
                    hook_strength_avg = excluded.hook_strength_avg,
                    coolpoint_count = excluded.coolpoint_count,
                    coolpoint_density = excluded.coolpoint_density,
                    reading_power_score = COALESCE(excluded.reading_power_score, reading_power_score),
                    last_analyzed_at = excluded.last_analyzed_at,
                    updated_at = excluded.updated_at
                """,
                (
                    chapter,
                    hook_count,
                    hook_strength_avg,
                    coolpoint_count,
                    coolpoint_density,
                    reading_power_score,
                    now,
                    now,
                    now,
                ),
            )

    def get_chapter_summary(self, chapter: str) -> Optional[Dict[str, Any]]:
        """
        Get chapter summary metrics.

        Args:
            chapter: Chapter identifier

        Returns:
            Chapter summary dictionary or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM chapter_summary WHERE chapter = ?",
                (chapter,),
            ).fetchone()
            return dict(row) if row else None

    # ==================== Analysis Log Methods ====================

    def log_analysis(
        self,
        chapter: str,
        analyzer_type: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> int:
        """
        Log an analysis operation.

        Args:
            chapter: Chapter identifier
            analyzer_type: Type of analyzer used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Duration in milliseconds
            status: Status ('success', 'failed', 'partial')
            error_message: Optional error message

        Returns:
            Row ID of the log entry
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_log
                (chapter, analyzer_type, input_tokens, output_tokens, duration_ms, status, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (chapter, analyzer_type, input_tokens, output_tokens, duration_ms, status, error_message, datetime.now().isoformat()),
            )
            return cursor.lastrowid or 0

    def exists(self) -> bool:
        try:
            return self.db_path.exists()
        except Exception:
            return False

    def is_empty(self) -> bool:
        try:
            if not self.exists():
                return True
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM hooks")
                hooks_count = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM chapter_summary")
                summary_count = cursor.fetchone()[0]
                return hooks_count == 0 and summary_count == 0
        except Exception:
            return True

    def get_overview_stats(self):
        try:
            if not self.db_path.exists():
                return None
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM chapter_summary")
                total_chapters = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COALESCE(SUM(hook_count), 0) FROM chapter_summary")
                total_hooks = cursor.fetchone()[0]
                cursor = conn.execute("SELECT AVG(hook_strength_avg) FROM chapter_summary")
                avg_hook_strength = cursor.fetchone()[0] or 0.0
                cursor = conn.execute("SELECT COALESCE(SUM(coolpoint_count), 0) FROM chapter_summary")
                total_coolpoints = cursor.fetchone()[0]
                cursor = conn.execute("SELECT AVG(coolpoint_density) FROM chapter_summary")
                avg_coolpoint_density = cursor.fetchone()[0] or 0.0
                return {
                    'total_chapters': total_chapters,
                    'total_hooks': total_hooks,
                    'avg_hook_strength': avg_hook_strength,
                    'total_coolpoints': total_coolpoints,
                    'avg_coolpoint_density': avg_coolpoint_density,
                }
        except Exception:
            return None

    def get_chapters_range(self, start: int, end: int):
        try:
            if not self.db_path.exists():
                return []
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT chapter, hook_count, hook_strength_avg, coolpoint_count, coolpoint_density FROM chapter_summary WHERE CAST(chapter AS INTEGER) BETWEEN ? AND ? ORDER BY CAST(chapter AS INTEGER)",
                    (start, end),
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
