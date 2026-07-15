"""向后兼容 shim - 真实实现见 infra/cli/commands/

保留这个文件是为了让 lingwen.py:27 的
`from infra.cli.commands import get_command, list_commands` 不需要修改。
"""
from infra.cli.commands import get_command, list_commands  # noqa: F401

__all__ = ["get_command", "list_commands"]
