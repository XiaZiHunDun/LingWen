#!/usr/bin/env python3
"""
通知动作 - 发送通知到指定渠道
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from infra.logging_config import logger
from .base import ActionResult, BaseAction


class NotifyAction(BaseAction):
    """
    发送通知动作

    支持多种通知渠道和模板渲染

    params:
        channel: 通知渠道（如 "writer_channel", "reviewer_channel", "controller_channel"）
        template: 通知模板名称（如 "review_complete", "stage_completed"）
        message: 自定义消息（可选，覆盖template）
    """

    # 支持的通知渠道
    VALID_CHANNELS = {
        "writer_channel",
        "reviewer_channel",
        "controller_channel",
        "system_channel"
    }

    # 通知模板目录
    TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "hooks" / "templates"

    @property
    def action_type(self) -> str:
        return "notify"

    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """
        发送通知

        Args:
            params: 包含 channel, template 等
            context: 执行上下文

        Returns:
            ActionResult with notification status
        """
        # 验证参数
        valid, error = self.validate_params(params, ["channel"])
        if not valid:
            logger.warning(f"Notify action: invalid params - {error}")
            return ActionResult(success=False, error=error)

        channel = params["channel"]
        template = params.get("template")
        message = params.get("message")

        logger.info(f"Notify action: channel={channel}, template={template}")

        # 验证渠道
        if channel not in self.VALID_CHANNELS:
            logger.warning(f"Notify action: invalid channel={channel}")
            return ActionResult(
                success=False,
                error=f"Invalid channel: {channel}"
            )

        try:
            # 构建通知内容
            if message:
                content = message
            elif template:
                content = self._render_template(template, context)
            else:
                content = self._generate_default_notification(context)

            # 发送通知（这里mock实现，实际可对接各种通知系统）
            result = self._send_notification(channel, content, context)

            logger.info(f"Notify action: sent to {channel}, status={result.get('status', 'sent')}")
            return ActionResult(
                success=True,
                output={
                    "channel": channel,
                    "content": content,
                    "sent_at": result.get("sent_at"),
                    "status": result.get("status", "sent")
                }
            )

        except Exception as e:
            logger.error(f"Notify action: failed - {e}")
            return ActionResult(success=False, error=str(e))

    def _render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        渲染通知模板

        Args:
            template_name: 模板名称
            context: 上下文变量

        Returns:
            渲染后的通知内容
        """
        # 尝试加载模板文件
        template_path = self.TEMPLATES_DIR / f"{template_name}.yaml"
        if template_path.exists():
            import yaml
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = yaml.safe_load(f)

            # 简单的模板替换
            template_str = template_data.get("content", "")
            return self._substitute_variables(template_str, context)

        # 如果模板不存在，生成默认内容
        return self._generate_from_template_name(template_name, context)

    def _substitute_variables(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """简单的变量替换"""
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result

    def _generate_default_notification(self, context: Dict[str, Any]) -> str:
        """生成默认通知内容"""
        hook_name = context.get("hook_name", "Unknown")
        event_name = context.get("event_name", "Unknown")
        return f"Hook '{hook_name}' triggered by event '{event_name}'"

    def _generate_from_template_name(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """根据模板名称生成通知内容"""
        if template_name == "review_complete":
            review_result = context.get("review_result", "UNKNOWN")
            chapter_id = context.get("chapter_id", "Unknown")
            return f"审核完成：章节 {chapter_id} 审核结果为 {review_result}"

        elif template_name == "stage_completed":
            step = context.get("step", "Unknown")
            return f"阶段完成：{step} 已完成"

        elif template_name == "quality_check_failed":
            issues = context.get("issues", [])
            return f"质量检查失败：发现 {len(issues)} 个问题"

        else:
            return f"通知模板 '{template_name}' 未找到"

    def _send_notification(
        self,
        channel: str,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        发送通知（Mock实现）

        实际实现可对接:
        - 文件系统（写入通知文件）
        - 消息队列（Redis Pub/Sub）
        - Webhook（HTTP POST）
        - 邮件/短信服务

        Returns:
            发送结果
        """
        from datetime import datetime

        # Mock实现：写入通知日志
        notification_log = {
            "channel": channel,
            "content": content,
            "sent_at": datetime.now().isoformat(),
            "status": "sent",
            "context": {
                "event_name": context.get("event_name"),
                "hook_name": context.get("hook_name"),
                "source": context.get("event_source")
            }
        }

        # 可以写入文件或发送到消息队列
        # 这里简单记录到日志
        logger.info(f"Sent to {channel}: {content}")

        return notification_log