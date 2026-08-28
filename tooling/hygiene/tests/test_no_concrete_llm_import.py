"""Hygiene test — verify DP-02 enforcement config is correct.

Catches regressions in:
- pyproject.toml import-linter contract removal
- LLMServiceAdapter deletion (the only allowed indirect touchpoint)
- LLMServicePort Protocol is_available() removal
"""
from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_pyproject_has_dp02_forbidden_contract() -> None:
    """DP-02 contract must exist in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    config = tomllib.loads(pyproject.read_text())

    contracts = config["tool"]["importlinter"]["contracts"]
    contract_names = {c["name"] for c in contracts}

    assert "no_concrete_llm_service_in_business_code" in contract_names, (
        f"DP-02 forbidden contract missing. Found: {contract_names}"
    )


def test_dp02_contract_targets_correct_modules() -> None:
    """DP-02 contract must forbid infra.llm_service in business code."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    config = tomllib.loads(pyproject.read_text())

    contracts = config["tool"]["importlinter"]["contracts"]
    dp02 = next(
        c for c in contracts
        if c["name"] == "no_concrete_llm_service_in_business_code"
    )

    assert dp02["type"] == "forbidden"
    assert "infra.llm_service" in dp02["forbidden_modules"]
    assert "lingwen_creator" in dp02["source_modules"]
    assert "apps" in dp02["source_modules"]


def test_llm_service_port_has_is_available() -> None:
    """LLMServicePort Protocol must declare is_available() for health checks."""
    port_file = PROJECT_ROOT / "packages/lingwen-shared/src/lingwen_shared/ports/llm_service.py"
    content = port_file.read_text()

    assert "def is_available" in content, (
        "LLMServicePort.is_available() missing — health check use case has no port-conformant API"
    )


def test_llm_service_adapter_file_exists() -> None:
    """LLMServiceAdapter sync facade must exist in packages/lingwen-llm."""
    adapter_file = PROJECT_ROOT / "packages/lingwen-llm/src/lingwen_llm/port_adapter.py"
    assert adapter_file.exists(), f"LLMServiceAdapter facade missing at {adapter_file}"


def test_no_concrete_llm_in_business_code() -> None:
    """Business code MUST NOT import concrete LLMService class directly.

    LLMTask/TaskType data types are allowed via port_adapter re-export.
    The actual concrete LLMService class import is what we're blocking.
    """
    # Grep business code (lingwen_creator + apps) for concrete LLMService imports.
    # We exclude the port_adapter re-export path since that's the allowed escape hatch.
    result = subprocess.run(
        [
            "grep", "-rn",
            "from infra.llm_service import.*LLMService($|[^A-Za-z])",
            "--include=*.py",
            "packages/lingwen-creator/",
            "apps/",
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )

    # subprocess returns exit code 1 if no matches found (which is what we want)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"grep failed: {result.stderr}")

    violations = [line for line in result.stdout.splitlines() if line.strip()]

    assert not violations, (
        f"DP-02 violations found (concrete LLMService import in business code):\n"
        + "\n".join(violations)
    )
