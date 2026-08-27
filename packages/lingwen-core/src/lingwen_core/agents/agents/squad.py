#!/usr/bin/env python3
"""
Agent 编队 — 多 Agent 编排与结果聚合

提供 AgentSquad 类，协调多个 Agent 并行/串行执行，并聚合结果。
默认禁用，通过配置标志启用。

Usage:
    from lingwen_core.agents.agents.squad import AgentSquad

    squad = AgentSquad(router=router, enabled=False)
    if squad.enabled:
        results = squad.run(context)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .....ai_service.router import AIRouter

logger = logging.getLogger(__name__)


@dataclass
class SquadResult:
    """Agent 编队执行结果

    Attributes:
        agent_name: Agent 名称
        findings: 发现项列表
        errors: 执行过程中的错误
        elapsed_ms: 执行耗时（毫秒）
    """
    agent_name: str
    findings: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    elapsed_ms: float = 0.0

    @property
    def total_findings(self) -> int:
        """总发现项数量"""
        return len(self.findings)

    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0


@dataclass
class AggregatedResult:
    """聚合后的编队结果

    Attributes:
        squad_results: 各 Agent 的单独结果
        total_findings: 总发现项数
        critical_count: critical 级别发现项数
        passed: 是否通过（无 critical 发现项）
        total_elapsed_ms: 总耗时
    """
    squad_results: List[SquadResult] = field(default_factory=list)
    total_findings: int = 0
    critical_count: int = 0
    passed: bool = True
    total_elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "squad_results": [
                {
                    "agent_name": r.agent_name,
                    "total_findings": r.total_findings,
                    "errors": r.errors,
                    "elapsed_ms": r.elapsed_ms,
                }
                for r in self.squad_results
            ],
            "total_findings": self.total_findings,
            "critical_count": self.critical_count,
            "passed": self.passed,
            "total_elapsed_ms": self.total_elapsed_ms,
        }


class AgentSquad:
    """Agent 编队

    协调多个 Agent 执行检查任务，聚合结果。
    默认禁用，通过 `enabled` 配置标志启用。

    支持的 Agent 类型:
    - outline_reviewer: 大纲审稿
    - character_consistency: 角色一致性检查
    - quality_reviewer: 质量审稿

    Attributes:
        router: AI Router 实例
        enabled: 是否启用编队模式（默认 False）
        agents: 已注册的 Agent 字典
    """

    def __init__(
        self,
        router: Optional['AIRouter'] = None,
        enabled: bool = False,
    ):
        """初始化 Agent 编队

        Args:
            router: AI Router 实例
            enabled: 是否启用编队模式
        """
        self._router = router
        self.enabled = enabled
        self._agents: Dict[str, Any] = {}

    def register(self, name: str, agent: Any) -> None:
        """注册一个 Agent

        Args:
            name: Agent 名称
            agent: Agent 实例
        """
        self._agents[name] = agent
        logger.info("AgentSquad: registered agent '%s'", name)

    def unregister(self, name: str) -> None:
        """注销一个 Agent

        Args:
            name: Agent 名称
        """
        self._agents.pop(name, None)
        logger.info("AgentSquad: unregistered agent '%s'", name)

    def list_agents(self) -> List[str]:
        """列出所有已注册的 Agent 名称"""
        return list(self._agents.keys())

    def run(self, context: Dict[str, Any]) -> AggregatedResult:
        """执行编队检查

        如果编队被禁用，返回空结果。

        Args:
            context: 上下文数据，传递给各 Agent 的 run() 方法

        Returns:
            AggregatedResult: 聚合结果
        """
        import time

        if not self.enabled:
            logger.info("AgentSquad: disabled, skipping all checks")
            return AggregatedResult(
                squad_results=[],
                total_findings=0,
                critical_count=0,
                passed=True,
                total_elapsed_ms=0.0,
            )

        if not self._agents:
            logger.warning("AgentSquad: enabled but no agents registered")
            return AggregatedResult(
                squad_results=[],
                total_findings=0,
                critical_count=0,
                passed=True,
                total_elapsed_ms=0.0,
            )

        logger.info(
            "AgentSquad: running %d agents in sequence", len(self._agents)
        )

        squad_results: List[SquadResult] = []
        total_start = time.time()

        # 串行执行各 Agent（可改为并行，但需注意 LLM 调用限流）
        for name, agent in self._agents.items():
            logger.info("AgentSquad: running agent '%s'", name)
            agent_start = time.time()

            try:
                findings = agent.run(context)
                elapsed = (time.time() - agent_start) * 1000
                squad_results.append(SquadResult(
                    agent_name=name,
                    findings=findings if isinstance(findings, list) else [],
                    elapsed_ms=elapsed,
                ))
                logger.info(
                    "AgentSquad: agent '%s' completed, %d findings, %.1fms",
                    name, len(findings) if isinstance(findings, list) else 0, elapsed,
                )
            except Exception as e:
                elapsed = (time.time() - agent_start) * 1000
                logger.error(
                    "AgentSquad: agent '%s' failed: %s", name, e
                )
                squad_results.append(SquadResult(
                    agent_name=name,
                    errors=[str(e)],
                    elapsed_ms=elapsed,
                ))

        total_elapsed = (time.time() - total_start) * 1000

        # 聚合统计
        total_findings = sum(r.total_findings for r in squad_results)
        critical_count = sum(
            sum(1 for f in r.findings if getattr(f, "severity", "") == "critical")
            for r in squad_results
        )
        passed = critical_count == 0

        logger.info(
            "AgentSquad: completed. %d agents, %d findings, %d critical, passed=%s, %.1fms",
            len(squad_results), total_findings, critical_count, passed, total_elapsed,
        )

        return AggregatedResult(
            squad_results=squad_results,
            total_findings=total_findings,
            critical_count=critical_count,
            passed=passed,
            total_elapsed_ms=total_elapsed,
        )

    def run_parallel(
        self, context: Dict[str, Any]
    ) -> AggregatedResult:
        """并行执行编队检查（使用线程池）

        Args:
            context: 上下文数据

        Returns:
            AggregatedResult: 聚合结果
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if not self.enabled:
            logger.info("AgentSquad: disabled, skipping all checks")
            return AggregatedResult(
                squad_results=[],
                total_findings=0,
                critical_count=0,
                passed=True,
                total_elapsed_ms=0.0,
            )

        if not self._agents:
            logger.warning("AgentSquad: enabled but no agents registered")
            return AggregatedResult(
                squad_results=[],
                total_findings=0,
                critical_count=0,
                passed=True,
                total_elapsed_ms=0.0,
            )

        logger.info(
            "AgentSquad: running %d agents in parallel", len(self._agents)
        )

        squad_results: List[SquadResult] = []
        total_start = time.time()

        def _run_agent(name: str, agent: Any) -> SquadResult:
            """内部：执行单个 Agent"""
            agent_start = time.time()
            try:
                findings = agent.run(context)
                elapsed = (time.time() - agent_start) * 1000
                return SquadResult(
                    agent_name=name,
                    findings=findings if isinstance(findings, list) else [],
                    elapsed_ms=elapsed,
                )
            except Exception as e:
                elapsed = (time.time() - agent_start) * 1000
                return SquadResult(
                    agent_name=name,
                    errors=[str(e)],
                    elapsed_ms=elapsed,
                )

        with ThreadPoolExecutor(max_workers=len(self._agents)) as executor:
            futures = {
                executor.submit(_run_agent, name, agent): name
                for name, agent in self._agents.items()
            }
            for future in as_completed(futures):
                result = future.result()
                squad_results.append(result)
                logger.info(
                    "AgentSquad: agent '%s' completed, %d findings, %.1fms",
                    result.agent_name, result.total_findings, result.elapsed_ms,
                )

        total_elapsed = (time.time() - total_start) * 1000

        # 聚合统计
        total_findings = sum(r.total_findings for r in squad_results)
        critical_count = sum(
            sum(1 for f in r.findings if getattr(f, "severity", "") == "critical")
            for r in squad_results
        )
        passed = critical_count == 0

        logger.info(
            "AgentSquad: parallel completed. %d agents, %d findings, %d critical, passed=%s, %.1fms",
            len(squad_results), total_findings, critical_count, passed, total_elapsed,
        )

        return AggregatedResult(
            squad_results=squad_results,
            total_findings=total_findings,
            critical_count=critical_count,
            passed=passed,
            total_elapsed_ms=total_elapsed,
        )
