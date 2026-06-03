#!/usr/bin/env python3
"""
TriggerModuleAction - 通过subprocess触发外部模块

用于hooks.yaml中的trigger_module action类型
"""

import importlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

from .base import BaseAction, ActionResult

logger = logging.getLogger(__name__)


class TriggerModuleAction(BaseAction):
    """触发外部模块执行

    通过subprocess调用CLI命令或直接导入模块执行指定方法
    """

    @property
    def action_type(self) -> str:
        return "trigger_module"

    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """执行trigger_module action

        Args:
            params: 动作参数
                - module: 模块名，如 "tools.anti_trope_enhancer"
                - method: 方法名，默认 "generate"
                - command: CLI命令，如 "anti-trope"
            context: 钩子上下文

        Returns:
            ActionResult: 执行结果
        """
        module_name = params.get("module")
        method_name = params.get("method", "generate")
        cli_command = params.get("command")

        try:
            if cli_command:
                # 通过CLI命令执行
                return self._execute_via_cli(cli_command, params, context)
            elif module_name:
                # 直接导入模块执行
                return self._execute_via_import(module_name, method_name, params, context)
            else:
                return ActionResult(
                    success=False,
                    error="trigger_module requires either 'module' or 'command' parameter"
                )

        except Exception as e:
            logger.error(f"TriggerModuleAction failed: {e}")
            return ActionResult(success=False, error=str(e))

    def _execute_via_cli(self, cli_command: str, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """通过CLI命令执行"""
        project_root = Path(__file__).parent.parent.parent.parent
        lingwen_py = project_root / "lingwen.py"

        # 构建命令参数
        cmd_parts = ["python", str(lingwen_py), cli_command]

        # 从context和params构建参数
        if "chapter_num" in context:
            cmd_parts.extend(["--chapter", str(context["chapter_num"])])
        if "outline" in context:
            cmd_parts.extend(["--outline", context["outline"]])
        if "count" in params:
            cmd_parts.extend(["--count", str(params["count"])])

        try:
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=params.get("timeout", 120)
            )
            return ActionResult(
                success=(result.returncode == 0),
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else None
            )
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, error=f"Command timed out after {params.get('timeout', 120)}s")
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _execute_via_import(self, module_name: str, method_name: str, params: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """通过直接导入模块执行"""
        try:
            # 动态导入模块
            module = importlib.import_module(module_name)

            # 获取方法
            if not hasattr(module, method_name):
                return ActionResult(
                    success=False,
                    error=f"Module {module_name} does not have method {method_name}"
                )

            method = getattr(module, method_name)

            # 从context构建参数
            method_params = self._build_method_params(params, context)

            # 调用方法
            result = method(**method_params)

            return ActionResult(
                success=True,
                output=str(result)
            )

        except ImportError as e:
            return ActionResult(success=False, error=f"Failed to import module {module_name}: {e}")
        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _build_method_params(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """从context和params构建方法参数"""
        method_params = {}

        # 复制context中的关键变量
        if "chapter_num" in context:
            method_params["chapter_num"] = context["chapter_num"]
        if "chapter_content" in context:
            method_params["content"] = context["chapter_content"]
        if "outline" in context:
            method_params["outline"] = context["outline"]
        if "chapter_title" in context:
            method_params["title"] = context["chapter_title"]

        # 合并params中的额外参数
        for key in ["count", "max_tokens", "temperature"]:
            if key in params:
                method_params[key] = params[key]

        return method_params