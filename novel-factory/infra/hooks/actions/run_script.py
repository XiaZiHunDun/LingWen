#!/usr/bin/env python3
"""
RunScriptAction - 在 hooks.yaml 中执行任意脚本

用于在 hook 触发时运行 shell 脚本或 Python 脚本，并返回执行结果。

params:
    script: 脚本路径（必填，相对项目根或绝对路径）
    args:   脚本参数列表（可选）
    python: 是否以 python 解释器执行（默认 False，按可执行位执行）
    cwd:    工作目录（默认 <project_root>）
    timeout: 超时秒数（默认 120）
    env:    额外环境变量 dict（可选）
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ActionResult, BaseAction

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RunScriptAction(BaseAction):
    """在 hook 触发时运行 shell / Python 脚本"""

    DEFAULT_TIMEOUT = 120

    @property
    def action_type(self) -> str:
        return "run_script"

    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> ActionResult:
        valid, error = self.validate_params(params, ["script"])
        if not valid:
            return ActionResult(success=False, error=error)

        script_raw: str = params["script"]
        script_path = self._resolve_script_path(script_raw)
        if not script_path.exists():
            return ActionResult(success=False, error=f"脚本不存在: {script_path}")

        args: List[str] = list(params.get("args", []) or [])
        use_python: bool = bool(params.get("python", script_path.suffix == ".py"))
        timeout: int = int(params.get("timeout", self.DEFAULT_TIMEOUT))
        cwd: Path = Path(params["cwd"]) if params.get("cwd") else PROJECT_ROOT
        extra_env: Optional[Dict[str, str]] = params.get("env")

        cmd = self._build_command(script_path, args, use_python)
        logger.info(
            "RunScriptAction: cmd=%s cwd=%s timeout=%ds",
            " ".join(cmd), cwd, timeout,
        )

        env = os.environ.copy()
        if extra_env:
            env.update({str(k): str(v) for k, v in extra_env.items()})

        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            logger.error("RunScriptAction: timeout after %ds (script=%s)", timeout, script_path)
            return ActionResult(success=False, error=f"超时（>{timeout}s）: {e}")
        except FileNotFoundError as e:
            return ActionResult(success=False, error=f"解释器不存在: {e}")
        except Exception as e:
            logger.exception("RunScriptAction: unexpected error")
            return ActionResult(success=False, error=str(e))

        success = result.returncode == 0
        return ActionResult(
            success=success,
            output={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "script": str(script_path),
            },
            error=None if success else (result.stderr or f"非零退出码 {result.returncode}"),
            duration_ms=0.0,
        )

    @staticmethod
    def _build_command(script_path: Path, args: List[str], use_python: bool) -> List[str]:
        if use_python:
            return ["python", str(script_path), *args]
        return [str(script_path), *args]

    @staticmethod
    def _resolve_script_path(script_raw: str) -> Path:
        p = Path(script_raw)
        if p.is_absolute():
            return p
        return PROJECT_ROOT / p
