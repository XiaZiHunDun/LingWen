#!/usr/bin/env python3
"""
健康检查模块

提供系统健康状态监控，支持：
1. 组件健康检查（数据库、LLM、向量数据库等）
2. 依赖服务状态检查
3. 系统整体健康评估
4. 健康检查端点（可用于监控）
"""

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from infra.errors import BaseError


class HealthCheckError(BaseError):
    """健康检查错误"""
    __error_name__ = "HealthCheckError"
    __error_tags__ = ["health"]


@dataclass(frozen=True)
class HealthStatus:
    """
    健康状态

    Args:
        status: 状态（healthy/unhealthy/degraded）
        message: 状态消息
        component: 组件名称
        latency_ms: 响应时间（毫秒）
        details: 详细信息
    """
    status: str
    message: str
    component: str = "system"
    latency_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status == "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status,
            "message": self.message,
            "component": self.component,
            "latency_ms": self.latency_ms,
            "details": self.details,
        }


class HealthCheck:
    """
    健康检查接口

    所有健康检查器必须实现此接口。
    """

    def name(self) -> str:
        """检查器名称"""
        raise NotImplementedError

    def check(self) -> HealthStatus:
        """执行检查"""
        raise NotImplementedError

    def is_critical(self) -> bool:
        """是否为关键检查（失败会导致系统降级）"""
        return True


class CompositeHealthCheck(HealthCheck):
    """
    组合健康检查

    包含多个子检查器，统一执行并汇总结果。
    """

    def __init__(self, name: str, checks: List[HealthCheck], critical: bool = True):
        self._name = name
        self._checks = checks
        self._critical = critical

    def name(self) -> str:
        return self._name

    def check(self) -> HealthStatus:
        """执行所有子检查并汇总结果"""
        results = []
        total_latency = 0.0

        for check in self._checks:
            start = time.time()
            result = check.check()
            latency = (time.time() - start) * 1000
            total_latency += latency
            results.append({
                "component": result.component,
                "status": result.status,
                "message": result.message,
                "latency_ms": latency,
            })

        # 汇总状态
        status = "healthy"
        messages = []

        for r in results:
            if r["status"] == "unhealthy":
                status = "unhealthy"
                messages.append(f"{r['component']}: {r['message']}")
            elif r["status"] == "degraded":
                if status == "healthy":
                    status = "degraded"
                messages.append(f"{r['component']}: {r['message']}")

        if status == "healthy":
            message = "All components are healthy"
        else:
            message = "; ".join(messages)

        return HealthStatus(
            status=status,
            message=message,
            component=self._name,
            latency_ms=total_latency,
            details={"checks": results},
        )

    def is_critical(self) -> bool:
        return self._critical


class DatabaseHealthCheck(HealthCheck):
    """
    数据库健康检查

    检查数据库连接是否正常。
    """

    def __init__(self, connection_check: Callable[[], bool], name: str = "database"):
        self._connection_check = connection_check
        self._name = name

    def name(self) -> str:
        return self._name

    def check(self) -> HealthStatus:
        start = time.time()
        try:
            if self._connection_check():
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="healthy",
                    message="Database connection is healthy",
                    component=self._name,
                    latency_ms=latency,
                )
            else:
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="unhealthy",
                    message="Database connection failed",
                    component=self._name,
                    latency_ms=latency,
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthStatus(
                status="unhealthy",
                message=f"Database check failed: {str(e)}",
                component=self._name,
                latency_ms=latency,
                details={"error": str(e)},
            )


class LLMHealthCheck(HealthCheck):
    """
    LLM 服务健康检查

    检查 LLM 服务是否可访问。
    """

    def __init__(self, health_check: Callable[[], bool], name: str = "llm"):
        self._health_check = health_check
        self._name = name

    def name(self) -> str:
        return self._name

    def check(self) -> HealthStatus:
        start = time.time()
        try:
            if self._health_check():
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="healthy",
                    message="LLM service is healthy",
                    component=self._name,
                    latency_ms=latency,
                )
            else:
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="degraded",
                    message="LLM service unavailable",
                    component=self._name,
                    latency_ms=latency,
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthStatus(
                status="degraded",
                message=f"LLM check failed: {str(e)}",
                component=self._name,
                latency_ms=latency,
                details={"error": str(e)},
            )

    def is_critical(self) -> bool:
        return False  # LLM 不可用不会导致系统完全不可用


class VectorDBHealthCheck(HealthCheck):
    """
    向量数据库健康检查

    检查向量数据库连接是否正常。
    """

    def __init__(self, health_check: Callable[[], bool], name: str = "vector_db"):
        self._health_check = health_check
        self._name = name

    def name(self) -> str:
        return self._name

    def check(self) -> HealthStatus:
        start = time.time()
        try:
            if self._health_check():
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="healthy",
                    message="Vector database connection is healthy",
                    component=self._name,
                    latency_ms=latency,
                )
            else:
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="degraded",
                    message="Vector database connection failed",
                    component=self._name,
                    latency_ms=latency,
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthStatus(
                status="degraded",
                message=f"Vector DB check failed: {str(e)}",
                component=self._name,
                latency_ms=latency,
                details={"error": str(e)},
            )

    def is_critical(self) -> bool:
        return False  # 向量数据库不可用不会导致系统完全不可用


class CacheHealthCheck(HealthCheck):
    """
    缓存健康检查

    检查缓存服务是否正常。
    """

    def __init__(self, health_check: Callable[[], bool], name: str = "cache"):
        self._health_check = health_check
        self._name = name

    def name(self) -> str:
        return self._name

    def check(self) -> HealthStatus:
        start = time.time()
        try:
            if self._health_check():
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="healthy",
                    message="Cache service is healthy",
                    component=self._name,
                    latency_ms=latency,
                )
            else:
                latency = (time.time() - start) * 1000
                return HealthStatus(
                    status="degraded",
                    message="Cache service unavailable",
                    component=self._name,
                    latency_ms=latency,
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return HealthStatus(
                status="degraded",
                message=f"Cache check failed: {str(e)}",
                component=self._name,
                latency_ms=latency,
                details={"error": str(e)},
            )

    def is_critical(self) -> bool:
        return False  # 缓存不可用不会导致系统完全不可用


class HealthManager:
    """
    健康检查管理器

    管理所有健康检查器，提供统一的健康状态查询接口。
    """

    def __init__(self):
        self._checks: List[HealthCheck] = []

    def register(self, check: HealthCheck) -> None:
        """
        注册健康检查器

        Args:
            check: 健康检查器
        """
        self._checks.append(check)

    def register_multiple(self, checks: List[HealthCheck]) -> None:
        """
        批量注册健康检查器

        Args:
            checks: 健康检查器列表
        """
        self._checks.extend(checks)

    def check_all(self) -> HealthStatus:
        """
        执行所有健康检查并汇总结果

        Returns:
            系统整体健康状态
        """
        if not self._checks:
            return HealthStatus(
                status="healthy",
                message="No health checks configured",
                component="system",
            )

        # 分离关键检查和非关键检查
        critical_checks = [c for c in self._checks if c.is_critical()]
        non_critical_checks = [c for c in self._checks if not c.is_critical()]

        # 执行关键检查
        critical_results = []
        for check in critical_checks:
            result = check.check()
            critical_results.append(result)

        # 执行非关键检查
        non_critical_results = []
        for check in non_critical_checks:
            result = check.check()
            non_critical_results.append(result)

        # 汇总结果
        all_results = critical_results + non_critical_results
        total_latency = sum(r.latency_ms for r in all_results)

        # 确定状态
        status = "healthy"
        messages = []

        # 关键检查失败会导致系统不健康
        for r in critical_results:
            if r.status == "unhealthy":
                status = "unhealthy"
                messages.append(f"{r.component}: {r.message}")

        # 非关键检查失败会导致系统降级
        if status == "healthy":
            for r in non_critical_results:
                if r.status != "healthy":
                    status = "degraded"
                    messages.append(f"{r.component}: {r.message}")

        if status == "healthy":
            message = "All systems are healthy"
        else:
            message = "; ".join(messages)

        return HealthStatus(
            status=status,
            message=message,
            component="system",
            latency_ms=total_latency,
            details={
                "critical_checks": [r.to_dict() for r in critical_results],
                "non_critical_checks": [r.to_dict() for r in non_critical_results],
            },
        )

    def check_component(self, name: str) -> Optional[HealthStatus]:
        """
        检查单个组件的健康状态

        Args:
            name: 组件名称

        Returns:
            健康状态或 None
        """
        for check in self._checks:
            if check.name() == name:
                return check.check()
        return None

    def list_components(self) -> List[str]:
        """
        获取所有已注册的组件名称

        Returns:
            组件名称列表
        """
        return [check.name() for check in self._checks]

    def is_healthy(self) -> bool:
        """
        检查系统是否健康

        Returns:
            是否健康
        """
        return self.check_all().is_healthy()


# 全局健康管理器实例
_global_health_manager = HealthManager()


def get_health_manager() -> HealthManager:
    """
    获取全局健康管理器

    Returns:
        健康管理器实例
    """
    return _global_health_manager


def register_health_check(check: HealthCheck) -> None:
    """
    注册健康检查器（快捷方法）

    Args:
        check: 健康检查器
    """
    _global_health_manager.register(check)


def health_status() -> HealthStatus:
    """
    获取系统健康状态（快捷方法）

    Returns:
        健康状态
    """
    return _global_health_manager.check_all()


def health_endpoint() -> Dict[str, Any]:
    """
    健康检查端点（用于 HTTP API）

    Returns:
        健康状态字典，可直接作为 JSON 响应返回
    """
    status = _global_health_manager.check_all()
    result = status.to_dict()
    result["timestamp"] = time.time()
    return result


__all__ = [
    "HealthStatus",
    "HealthCheck",
    "CompositeHealthCheck",
    "DatabaseHealthCheck",
    "LLMHealthCheck",
    "VectorDBHealthCheck",
    "CacheHealthCheck",
    "HealthManager",
    "get_health_manager",
    "register_health_check",
    "health_status",
    "health_endpoint",
]
