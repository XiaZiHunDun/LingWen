"""
Phase 15.0 T1.4: /api/health route.

Extracted from dashboard/app.py create_app closure (was at app.py line 243-246).

集成 infra.health 模块，支持多组件健康检查。
"""
from __future__ import annotations

import os
import psutil
import sys
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI

from apps.studio_api.models import HealthResponse, DatabaseStatus, MemoryUsage
from apps.studio_api.routes.ctx import RoutesContext
from infra.health import (
    HealthManager,
    DatabaseHealthCheck,
    LLMHealthCheck,
    VectorDBHealthCheck,
    CacheHealthCheck,
    get_health_manager,
    register_health_check,
    health_endpoint,
)

_START_TIME = datetime.now(timezone.utc)


def _register_health_checks(ctx: RoutesContext) -> None:
    """注册健康检查器"""
    # 数据库健康检查
    def check_db_connection() -> bool:
        try:
            return ctx.db.exists()
        except (OSError, RuntimeError, AttributeError):
            # DB 文件不存在 / 连接失败 / 方法缺失
            return False

    db_check = DatabaseHealthCheck(check_db_connection, name="reading_power_db")
    register_health_check(db_check)

    # CVG 存储健康检查
    def check_cvg_storage() -> bool:
        try:
            storage = ctx.cvg_storage()
            return storage is not None
        except (OSError, RuntimeError, ImportError):
            # CVG 存储初始化失败 / 依赖缺失
            return False

    cvg_check = DatabaseHealthCheck(check_cvg_storage, name="cvg_storage")
    register_health_check(cvg_check)

    # LLM 服务健康检查（非关键）
    def check_llm() -> bool:
        try:
            from lingwen_llm.llm_service import LLMService
            llm = LLMService.get_instance()
            return llm.is_available()
        except (OSError, RuntimeError, ImportError, AttributeError):
            # LLM 服务不可用 / 依赖缺失 / 方法缺失
            return False

    llm_check = LLMHealthCheck(check_llm, name="llm_service")
    register_health_check(llm_check)


def register_health(app: FastAPI, ctx: RoutesContext) -> None:
    # 注册健康检查器
    _register_health_checks(ctx)

    @app.get("/api/health", response_model=HealthResponse)
    def health_check() -> HealthResponse:
        """Health check endpoint with system metrics."""
        now = datetime.now(timezone.utc)
        uptime = (now - _START_TIME).total_seconds()
        process = psutil.Process()

        # 获取系统健康状态
        health_status = health_endpoint()
        overall_status = health_status.get("status", "healthy")

        db_status = DatabaseStatus(status="healthy")
        try:
            if ctx.db.exists():
                db_status.tables = len(ctx.db.get_tables()) if hasattr(ctx.db, 'get_tables') else 0
                db_status.records = ctx.db.get_total_records() if hasattr(ctx.db, 'get_total_records') else 0
            else:
                db_status.status = "not_found"
        except (OSError, RuntimeError, AttributeError) as e:
            # DB 查询失败
            db_status.status = "unhealthy"
            db_status.error = str(e)

        memory_usage = MemoryUsage(
            rss_mb=round(process.memory_info().rss / (1024 * 1024), 2),
            vms_mb=round(process.memory_info().vms / (1024 * 1024), 2),
            cpu_percent=process.cpu_percent(),
            num_threads=process.num_threads(),
        )

        environment = os.environ.get("LINGWEN_ENV", "development")

        features = {
            "cvg": True,
            "workflows": True,
            "studio": True,
            "creator": True,
            "websocket": True,
            "rate_limit": True,
        }

        return HealthResponse(
            status=overall_status,
            service="reading-power-dashboard",
            timestamp=now.isoformat(),
            uptime=uptime,
            version=os.environ.get("LINGWEN_VERSION", "unknown"),
            python_version=sys.version.split()[0],
            database=db_status,
            memory=memory_usage,
            environment=environment,
            features=features,
        )

    @app.get("/api/health/detailed")
    def health_check_detailed() -> Dict[str, Any]:
        """详细健康检查端点，返回所有组件的健康状态"""
        now = datetime.now(timezone.utc)
        uptime = (now - _START_TIME).total_seconds()
        process = psutil.Process()

        # 获取系统健康状态
        health_result = health_endpoint()

        return {
            "status": health_result.get("status"),
            "service": "reading-power-dashboard",
            "timestamp": now.isoformat(),
            "uptime": uptime,
            "version": os.environ.get("LINGWEN_VERSION", "unknown"),
            "python_version": sys.version.split()[0],
            "memory": {
                "rss_mb": round(process.memory_info().rss / (1024 * 1024), 2),
                "vms_mb": round(process.memory_info().vms / (1024 * 1024), 2),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
            },
            "components": health_result.get("details", {}),
        }
