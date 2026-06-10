"""CLI commands subpackage + registry.

Mirrors the 10 Command subclasses to 10 per-command files (one file per
class, 1:1 mapping). The COMMANDS dict and get_command()/list_commands()
helpers live here so lingwen.py can import from a single path.

File map:
  base.py              - Command ABC
  check.py             - CheckCommand
  repair.py            - RepairCommand
  verify.py            - VerifyCommand
  polish.py            - PolishCommand
  status.py            - StatusCommand
  doctor.py            - DoctorCommand
  anti_trope.py        - AntiTropeCommand
  llm_analyze.py       - LLMAnalyzeCommand
  story_contract.py    - StoryContractCommand
  reading_power.py     - ReadingPowerCommand
  backfill.py          - BackfillCommand (Phase 9.11)
"""
from typing import List, Optional

from .anti_trope import AntiTropeCommand
from .backfill import BackfillCommand
from .base import Command
from .check import CheckCommand
from .doctor import DoctorCommand
from .llm_analyze import LLMAnalyzeCommand
from .polish import PolishCommand
from .reading_power import ReadingPowerCommand
from .repair import RepairCommand
from .ripple_audit import RippleAuditCommand
from .ripple_rollback import RippleRollbackCommand
from .status import StatusCommand
from .story_contract import StoryContractCommand
from .verify import VerifyCommand

COMMANDS = {
    "check": CheckCommand,
    "repair": RepairCommand,
    "verify": VerifyCommand,
    "status": StatusCommand,
    "doctor": DoctorCommand,
    "polish": PolishCommand,
    "anti-trope": AntiTropeCommand,
    "llm-analyze": LLMAnalyzeCommand,
    "reading-power": ReadingPowerCommand,
    "story-contract": StoryContractCommand,
    "backfill": BackfillCommand,
    # Phase 9.14 additive: 2 new top-level subcommands
    "ripple-audit": RippleAuditCommand,
    "ripple-rollback": RippleRollbackCommand,
}

__all__ = [
    "Command", "CheckCommand", "RepairCommand", "VerifyCommand", "StatusCommand",
    "DoctorCommand", "PolishCommand", "AntiTropeCommand", "LLMAnalyzeCommand",
    "ReadingPowerCommand", "StoryContractCommand", "BackfillCommand",
    "RippleAuditCommand", "RippleRollbackCommand",
    "COMMANDS", "get_command", "list_commands",
]


def get_command(name: str) -> Optional[Command]:
    """
    Get command instance by name.

    Args:
        name: Command name (check, repair, verify, status, doctor, ...)

    Returns:
        Command instance or None if not found
    """
    cmd_class = COMMANDS.get(name)
    if cmd_class is None:
        return None
    return cmd_class()


def list_commands() -> List[dict]:
    """
    List all available commands.

    Returns:
        List of command info dicts
    """
    return [
        {"name": cmd.name, "description": cmd.description}
        for cmd in [cls() for cls in COMMANDS.values()]
    ]
