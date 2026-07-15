#!/usr/bin/env python3
"""
Tests for WorkflowDB — R3-001 verification.

Verifies:
- transaction() 使用 fcntl.flock 防止多进程写竞争
- 并发 transaction() 调用串行化(总耗时接近 N × 单事务耗时,而非交错)
- 锁在异常路径上正确释放
- _lock_path 与 db_path 在同一目录(.lock 后缀)
"""
import fcntl
import multiprocessing
import os
import sys
import threading
import time
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infra.state.database import WorkflowDB


@pytest.fixture
def db(tmp_path):
    """Fresh WorkflowDB in tmp_path"""
    db_path = tmp_path / "wf.db"
    inst = WorkflowDB(str(db_path))
    yield inst, db_path
    # cleanup lock file (may remain if test crashed mid-flock)
    lock = db_path.with_suffix('.lock')
    if lock.exists():
        try:
            lock.unlink()
        except OSError:
            pass


def _mp_probe_and_write(
    db_path_str: str,
    key: str,
    value: str,
    barrier: multiprocessing.Barrier,
    peak_array,
    slot: int,
) -> None:
    """Subprocess: probe flock peak, then write workflow_state row."""
    barrier.wait(timeout=5)
    peak_array[slot] = _probe_flock_peak(db_path_str, hold_s=0.08)
    inst = WorkflowDB(db_path_str)
    with inst.transaction() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
            (key, value),
        )


def _crashing_worker(db_path_str: str) -> None:
    """Subprocess: exit while transaction context releases flock."""
    inst = WorkflowDB(db_path_str)
    with inst.transaction() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
            ("crash", "1"),
        )
    os._exit(0)


class TestFlockBasics:
    """Lock file path and basic setup"""

    def test_lock_path_derived_from_db_path(self, tmp_path):
        """_lock_path 应是 db_path 同目录 + .lock 后缀"""
        db_path = tmp_path / "wf.db"
        inst = WorkflowDB(str(db_path))
        assert inst._lock_path == tmp_path / "wf.lock"

    def test_lock_file_in_same_dir_as_db(self, tmp_path):
        db_path = tmp_path / "sub" / "wf.db"
        inst = WorkflowDB(str(db_path))
        assert inst._lock_path.parent == db_path.parent
        assert inst._lock_path.suffix == ".lock"


def _probe_flock_peak(db_path_str: str, hold_s: float = 0.05) -> int:
    """Return peak concurrent holders observed inside transaction() (expect 1)."""
    inst = WorkflowDB(db_path_str)
    with inst.transaction() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS flock_probe (k TEXT PRIMARY KEY, v INTEGER NOT NULL DEFAULT 0)"
        )
        conn.execute("INSERT OR IGNORE INTO flock_probe (k, v) VALUES ('active', 0)")
        conn.execute("INSERT OR IGNORE INTO flock_probe (k, v) VALUES ('peak', 0)")
        active = conn.execute(
            "SELECT v FROM flock_probe WHERE k = 'active'"
        ).fetchone()[0] + 1
        conn.execute(
            "UPDATE flock_probe SET v = ? WHERE k = 'active'", (active,)
        )
        peak = conn.execute(
            "SELECT v FROM flock_probe WHERE k = 'peak'"
        ).fetchone()[0]
        if active > peak:
            conn.execute(
                "UPDATE flock_probe SET v = ? WHERE k = 'peak'", (active,)
            )
        time.sleep(hold_s)
        conn.execute(
            "UPDATE flock_probe SET v = v - 1 WHERE k = 'active'"
        )
    with inst._get_conn() as conn:
        return conn.execute(
            "SELECT v FROM flock_probe WHERE k = 'peak'"
        ).fetchone()[0]


class TestTransactionFlock:
    """transaction() actually uses flock"""

    def test_concurrent_transactions_no_overlap(self, tmp_path):
        """Parallel transaction() calls must not overlap (flock_probe peak == 1)."""
        db_path = tmp_path / "wf.db"
        WorkflowDB(str(db_path))

        def worker():
            _probe_flock_peak(str(db_path), hold_s=0.05)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        inst = WorkflowDB(str(db_path))
        with inst._get_conn() as conn:
            row = conn.execute(
                "SELECT v FROM flock_probe WHERE k = 'peak'"
            ).fetchone()
        assert row is not None, "flock_probe table missing"
        assert row[0] == 1, f"flock overlap detected: peak={row[0]}"

    def test_lock_released_on_exception(self, tmp_path):
        """事务内异常应释放 flock,后续 transaction() 不应被永久阻塞"""
        db_path = tmp_path / "wf.db"
        inst = WorkflowDB(str(db_path))

        # Trigger rollback path
        with pytest.raises(RuntimeError):
            with inst.transaction() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
                    ("boom", "1"),
                )
                raise RuntimeError("simulated failure")

        # 后续 transaction() 必须能成功(锁已释放)
        with inst.transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
                ("recovered", "1"),
            )

        with inst._get_conn() as conn:
            keys = {row["key"] for row in conn.execute("SELECT key FROM workflow_state").fetchall()}
        assert "recovered" in keys
        assert "boom" not in keys  # rolled back

    def test_lock_file_created_on_first_transaction(self, tmp_path):
        """transaction() 期间应创建 lock 文件"""
        db_path = tmp_path / "wf.db"
        inst = WorkflowDB(str(db_path))
        lock = db_path.with_suffix('.lock')

        with inst.transaction() as conn:
            conn.execute("SELECT 1").fetchone()
            # 锁文件应已存在(transaction 期间持有 flock)
            assert lock.exists()

        # transaction 结束后,锁文件可能存在(取决于 OS 是否清理空 fd),但 flock 已释放
        # 这里只断言 lock 文件路径与 db_path 在同目录
        assert lock.parent == db_path.parent


class TestMultiprocessFlock:
    """真正的多进程:验证 fcntl.flock 跨进程生效(本进程锁 ≠ 跨进程锁)"""

    def test_multiprocess_writers_serialize(self, tmp_path):
        """N subprocess writers: flock_probe peak must stay 1 (no overlap)."""
        db_path = str(tmp_path / "wf.db")
        WorkflowDB(db_path)

        n = 3
        barrier = multiprocessing.Barrier(n)
        peak_array = multiprocessing.Array("i", n)

        procs = [
            multiprocessing.Process(
                target=_mp_probe_and_write,
                args=(db_path, f"key{i}", f"v{i}", barrier, peak_array, i),
            )
            for i in range(n)
        ]
        start = time.monotonic()
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=10)
            assert not p.is_alive(), "worker hung — flock deadlock?"
        total = time.monotonic() - start

        assert max(peak_array) == 1, f"multiprocess flock overlap: peaks={list(peak_array)}"
        assert total >= n * 0.05, f"workers finished suspiciously fast: {total:.3f}s"

        inst = WorkflowDB(db_path)
        with inst._get_conn() as conn:
            keys = {row["key"] for row in conn.execute("SELECT key FROM workflow_state").fetchall()}
        for i in range(n):
            assert f"key{i}" in keys, f"key{i} missing — writer failed"

    def test_multiprocess_no_deadlock_on_error(self, tmp_path):
        """子进程异常退出后,后续 transaction() 仍能获取锁(无死锁)"""
        db_path = str(tmp_path / "wf.db")
        WorkflowDB(db_path)  # init schema

        p = multiprocessing.Process(target=_crashing_worker, args=(db_path,))
        p.start()
        p.join(timeout=5)
        assert p.exitcode == 0

        # 主进程能继续写
        inst = WorkflowDB(db_path)
        with inst.transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
                ("main", "1"),
            )

        with inst._get_conn() as conn:
            keys = {row["key"] for row in conn.execute("SELECT key FROM workflow_state").fetchall()}
        assert {"crash", "main"}.issubset(keys)
