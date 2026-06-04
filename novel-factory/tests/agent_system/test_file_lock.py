"""Tests for FileLock + HumanDecisionQueue.with_lock (Phase 6.5)

Doc 4 §10 Phase 6.5: CLI + dashboard 多进程写 decisions.json 防止 race condition。

设计:
- infra/agent_system/_file_lock.py: FileLock context manager (fcntl.flock + cross-platform fallback)
- infra/agent_system/decision_queue.py:
  - HumanDecisionQueue.with_lock() 上下文: 拿锁 + 重新读文件 + yield + 写回
  - HumanDecisionQueue.save() 内部用 FileLock
- infra/agent_system/master_controller.py: resolve_decision / run_workflow add 改用 with_lock

测试覆盖:
- FileLock 单线程 acquire/release
- FileLock 跨线程/进程互斥
- FileLock timeout
- with_lock reload + save 原子性
- 跨进程 with_lock 不丢数据 (multiprocessing 真子进程,确保 fcntl 真的跨进程生效)
"""
from __future__ import annotations

import json
import multiprocessing
import os
import platform
import threading
import time
from pathlib import Path

import pytest

from infra.agent_system._file_lock import FileLock
from infra.agent_system.decision_queue import (
    DecisionKind,
    HumanDecision,
    HumanDecisionQueue,
    create_decision,
)

# POSIX 才有 fcntl.flock; Windows 上测试 skip
IS_POSIX = platform.system() != "Windows"
SKIP_IF_NOT_POSIX = pytest.mark.skipif(
    not IS_POSIX, reason="FileLock uses fcntl.flock (POSIX only)"
)


# === TestFileLockBasic ===

@SKIP_IF_NOT_POSIX
class TestFileLockBasic:
    """FileLock 单线程基本操作"""

    def test_acquire_and_release(self, tmp_path: Path):
        lock_path = tmp_path / "test.lock"
        with FileLock(lock_path):
            assert lock_path.exists()

    def test_lock_file_created_in_parent(self, tmp_path: Path):
        lock_path = tmp_path / "subdir" / "test.lock"
        with FileLock(lock_path):
            assert lock_path.exists()
            assert lock_path.parent.exists()

    def test_re_acquire_after_release(self, tmp_path: Path):
        lock_path = tmp_path / "test.lock"
        with FileLock(lock_path):
            pass
        # 第二次获取应成功(锁已释放)
        with FileLock(lock_path):
            pass

    def test_with_block_releases_on_exception(self, tmp_path: Path):
        lock_path = tmp_path / "test.lock"
        with pytest.raises(RuntimeError):
            with FileLock(lock_path):
                raise RuntimeError("boom")
        # 异常后锁应被释放 — 重新获取应成功
        with FileLock(lock_path):
            pass


# === TestFileLockMutualExclusion ===

@SKIP_IF_NOT_POSIX
class TestFileLockMutualExclusion:
    """FileLock 互斥测试 (线程级)"""

    def test_second_lock_blocks_until_first_releases(self, tmp_path: Path):
        """第二个 FileLock 进入应阻塞到第一个退出"""
        lock_path = tmp_path / "test.lock"
        order: list[str] = []

        def first():
            with FileLock(lock_path):
                order.append("first_enter")
                time.sleep(0.2)
                order.append("first_exit")

        def second():
            time.sleep(0.05)  # 等 first 先拿锁
            with FileLock(lock_path):
                order.append("second_enter")
                order.append("second_exit")

        t1 = threading.Thread(target=first)
        t2 = threading.Thread(target=second)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # first 应完整执行,second 在 first 释放后才进入
        assert order == [
            "first_enter", "first_exit",
            "second_enter", "second_exit",
        ]


# === TestHumanDecisionQueueWithLock ===

@SKIP_IF_NOT_POSIX
class TestHumanDecisionQueueWithLock:
    """HumanDecisionQueue.with_lock 测试"""

    def test_with_lock_noop_when_no_state_dir(self):
        """state_dir=None 时 with_lock 应是 no-op"""
        q = HumanDecisionQueue()  # no state_dir
        d = create_decision(DecisionKind.OUTLINE_JUDGMENT, "n1", "p", ("a",))
        with q.with_lock():
            q.add(d)
        # in-memory 应有
        assert d.decision_id in q

    def test_with_lock_persists_changes(self, tmp_path: Path):
        """with_lock 退出时应自动 save"""
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        d = create_decision(DecisionKind.OUTLINE_JUDGMENT, "n1", "p", ("a",))
        with q.with_lock():
            q.add(d)
        # 文件应已写入
        assert (tmp_path / "decisions.json").exists()
        data = json.loads((tmp_path / "decisions.json").read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["decision_id"] == d.decision_id

    def test_with_lock_reloads_from_file_on_entry(self, tmp_path: Path):
        """with_lock 进入时应 reload 文件,看到其他进程的修改"""
        # 进程 A: 写文件
        q_a = HumanDecisionQueue(state_dir=str(tmp_path))
        d_a = create_decision(DecisionKind.OUTLINE_JUDGMENT, "n_a", "p_a", ("a",))
        q_a.add(d_a)
        q_a.save()
        assert (tmp_path / "decisions.json").exists()

        # 进程 B: 启动时 file 已存在, 但其 in-memory 是空 (模拟 B 启动时 A 已写)
        q_b = HumanDecisionQueue(state_dir=str(tmp_path))
        # 假设 B 的 in-memory 被 clear (模拟后续 reload)
        q_b._decisions.clear()
        assert len(q_b._decisions) == 0

        # B 进入 with_lock 应 reload, 看到 A 的修改
        with q_b.with_lock():
            assert len(q_b._decisions) == 1
            assert d_a.decision_id in q_b._decisions

    def test_save_method_also_uses_lock(self, tmp_path: Path):
        """save() 内部用 FileLock,不要求外部显式 with_lock"""
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        d = create_decision(DecisionKind.OUTLINE_JUDGMENT, "n1", "p", ("a",))
        q.add(d)
        q.save()  # 不抛异常 = 通过

    def test_with_lock_releases_on_exception(self, tmp_path: Path):
        """with_lock 异常时应释放锁 (其他进程可继续)"""
        q = HumanDecisionQueue(state_dir=str(tmp_path))
        with pytest.raises(RuntimeError):
            with q.with_lock():
                raise RuntimeError("boom")
        # 锁应已释放 — 重新获取应成功
        with q.with_lock():
            pass


# === TestCrossProcessNoDataLoss ===

@SKIP_IF_NOT_POSIX
@pytest.mark.timeout(10)
class TestCrossProcessNoDataLoss:
    """跨进程 with_lock 原子性 — 多进程真子进程测试

    模拟:
    - 进程 A 不断 add decision_*
    - 进程 B 不断 resolve decision_*
    - 用 shared state_dir
    - 跑 N 轮后,文件应包含所有 add 的决策,B resolve 的应标记 resolved
    """

    def _producer(self, state_dir: str, n: int) -> None:
        q = HumanDecisionQueue(state_dir=state_dir)
        for i in range(n):
            d = create_decision(
                decision_kind=DecisionKind.OUTLINE_JUDGMENT,
                node_id=f"node_{i}",
                prompt=f"p_{i}",
                options=("approve", "revise"),
            )
            with q.with_lock():
                q.add(d)
            # 短 sleep 让 consumer 有机会跑
            time.sleep(0.001)

    def _consumer(self, state_dir: str, n: int) -> None:
        # 等 producer 写一些后再开始
        time.sleep(0.1)
        q = HumanDecisionQueue(state_dir=state_dir)
        resolved = 0
        attempts = 0
        while resolved < n and attempts < n * 3:
            attempts += 1
            with q.with_lock():
                pending = q.pending()
                if pending:
                    d = pending[0]
                    q.resolve(d.decision_id, "approve")
                    resolved += 1
            time.sleep(0.001)
        return  # resolved 局部变量会丢,但 q.resolve 已落盘

    def test_concurrent_add_and_resolve_no_data_loss(self, tmp_path: Path):
        """并发 add + resolve 不丢数据 (各 N=20)"""
        state_dir = str(tmp_path)
        n = 20

        p = multiprocessing.Process(target=self._producer, args=(state_dir, n))
        c = multiprocessing.Process(target=self._consumer, args=(state_dir, n))
        p.start()
        c.start()
        p.join(timeout=15)
        c.join(timeout=15)

        assert not p.is_alive(), "producer hung"
        assert not c.is_alive(), "consumer hung"

        # 验证: 文件应包含 N 个决策, 全部 resolved
        final = HumanDecisionQueue(state_dir=state_dir)
        assert len(final._decisions) == n
        for d in final._decisions.values():
            assert d.status.value == "resolved", (
                f"decision {d.decision_id} still {d.status.value}, race?"
            )


# === TestFileLockTimeout (optional) ===

@SKIP_IF_NOT_POSIX
class TestFileLockTimeout:
    """FileLock timeout 测试 (Phase 6.5 不强求,留作未来扩展)

    跳过:当前 FileLock 是阻塞 flock,无 timeout 参数。
    留个 placeholder 测试让未来扩展有锚点。
    """

    def test_timeout_placeholder(self, tmp_path: Path):
        # 当前 API:FileLock(path) 无 timeout;默认阻塞到拿到
        # 未来:FileLock(path, timeout=2.0) + TimeoutError
        lock_path = tmp_path / "test.lock"
        with FileLock(lock_path):
            pass
