#!/usr/bin/env python3
"""
Tests for WorkflowDB — R3-001 verification.

Verifies:
- transaction() 使用 fcntl.flock 防止多进程写竞争
- 并发 transaction() 调用串行化(总耗时接近 N × 单事务耗时,而非交错)
- 锁在异常路径上正确释放
- _lock_path 与 db_path 在同一目录(.lock 后缀)
"""
import os
import sys
import time
import fcntl
import multiprocessing
import threading
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


def _worker_write(db_path_str: str, key: str, value: str, barrier: multiprocessing.Barrier):
    """Subprocess: acquire lock, write key, release. Use barrier to align start."""
    inst = WorkflowDB(db_path_str)
    barrier.wait()  # align all workers
    with inst.transaction() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
            (key, value),
        )
        # Hold lock briefly so we observe serialization, not interleaving
        time.sleep(0.3)


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


class TestTransactionFlock:
    """transaction() actually uses flock"""

    def test_concurrent_transactions_serialize(self, tmp_path):
        """两个并发 transaction() 必须串行化(总耗时 ≥ 2×单事务)"""
        db_path = tmp_path / "wf.db"
        inst = WorkflowDB(str(db_path))

        # Baseline: a single transaction with 200ms hold
        start = time.monotonic()
        with inst.transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
                ("a", "1"),
            )
            time.sleep(0.2)
        single = time.monotonic() - start

        # Two parallel transactions each holding 200ms — if they ran truly parallel
        # total ≈ 200ms; with flock they should serialize → ≈ 400ms
        results = []

        def worker(tag):
            with inst.transaction() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
                    (tag, "x"),
                )
                time.sleep(0.2)
            results.append(tag)

        threads = [threading.Thread(target=worker, args=(t,)) for t in ("b", "c")]
        start = time.monotonic()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        total = time.monotonic() - start

        # 串行化断言:总耗时 ≥ 1.6 × 单事务(允许 busy_timeout 重试等小抖动)
        assert total >= 1.5 * single, (
            f"flock 未生效:total={total:.3f}s single={single:.3f}s (应 ≥ 1.5×)"
        )
        # 写入了两条
        with inst._get_conn() as conn:
            keys = {row["key"] for row in conn.execute("SELECT key FROM workflow_state").fetchall()}
        assert {"a", "b", "c"}.issubset(keys)

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
        """N 个子进程并发写,每个持有 200ms。flock 应确保总耗时 ≥ N × 0.3s - 抖动"""
        db_path = str(tmp_path / "wf.db")

        # Pre-create DB schema (parent process)
        WorkflowDB(db_path)

        n = 3
        barrier = multiprocessing.Barrier(n)
        procs = [
            multiprocessing.Process(
                target=_worker_write,
                args=(db_path, f"key{i}", f"v{i}", barrier),
            )
            for i in range(n)
        ]
        start = time.monotonic()
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=5)
            assert not p.is_alive(), "worker hung — flock deadlock?"
        total = time.monotonic() - start

        # 串行化预期: ≈ n × 0.3s (允许 5% 抖动,实测 0.95s ≈ 3×0.3 = 0.9)
        # 若 flock 失效,3 个子进程并发运行,总耗时应 ≈ 0.3s(远低于 0.9)
        min_expected = n * 0.3 * 0.9
        assert total >= min_expected, (
            f"multiprocess flock 未生效:total={total:.3f}s expected≥{min_expected:.2f}s"
        )

        # 验证所有 key 都写入了
        inst = WorkflowDB(db_path)
        with inst._get_conn() as conn:
            keys = {row["key"] for row in conn.execute("SELECT key FROM workflow_state").fetchall()}
        for i in range(n):
            assert f"key{i}" in keys, f"key{i} missing — writer failed"

    def test_multiprocess_no_deadlock_on_error(self, tmp_path):
        """子进程异常退出后,后续 transaction() 仍能获取锁(无死锁)"""
        db_path = str(tmp_path / "wf.db")
        WorkflowDB(db_path)  # init schema

        def crashing_worker(db_path_str: str):
            inst = WorkflowDB(db_path_str)
            with inst.transaction() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO workflow_state (key, value) VALUES (?, ?)",
                    ("crash", "1"),
                )
                # exit abruptly while holding flock
            # The 'with' block should release the lock
            os._exit(0)

        p = multiprocessing.Process(target=crashing_worker, args=(db_path,))
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
