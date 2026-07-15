"""Phase 9.39 F24: ESLint 9+ flat config contract tests.

Phase 8.43 已迁 ESLint 10 + eslint.config.js flat config (0 .eslintrc).
F24 补: pnpm lint 脚本 + 契约测试防 regression 回 ESLint 8 legacy config.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "dashboard" / "frontend"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _parse_semver_major(version_spec: str) -> int:
    match = re.search(r"(\d+)", version_spec.lstrip("^~>="))
    assert match, f"cannot parse semver from {version_spec!r}"
    return int(match.group(1))


class TestFrontendEslintPackage:
    def test_eslint_devdep_is_v9_or_newer(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        eslint_ver = pkg["devDependencies"]["eslint"]
        assert _parse_semver_major(eslint_ver) >= 9, eslint_ver

    def test_eslint_plugin_vue_is_v9_or_newer(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        vue_ver = pkg["devDependencies"]["eslint-plugin-vue"]
        assert _parse_semver_major(vue_ver) >= 9, vue_ver

    def test_package_has_lint_script(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        assert pkg["scripts"].get("lint") == "pnpm lint:all"
        assert "eslint.config.js" in pkg["scripts"]["lint:testid"]


class TestFrontendEslintFlatConfig:
    def test_eslint_config_js_uses_flat_vue3_recommended(self):
        text = (FRONTEND_DIR / "eslint.config.js").read_text(encoding="utf-8")
        assert "export default [" in text
        assert "flat/vue3-recommended" in text
        assert "eslint-plugin-vue" in text

    def test_no_legacy_eslintrc_files(self):
        legacy = list(FRONTEND_DIR.glob(".eslintrc*")) + list(
            FRONTEND_DIR.glob("**/.eslintrc*")
        )
        # exclude node_modules if glob ever picks it up
        legacy = [p for p in legacy if "node_modules" not in p.parts]
        assert legacy == []


class TestFrontendEslintCI:
    def test_dashboard_frontend_ci_runs_lint_all(self):
        text = (WORKFLOWS_DIR / "dashboard-frontend-ci.yml").read_text(encoding="utf-8")
        assert "pnpm lint:all" in text

    def test_lint_staged_uses_flat_config(self):
        data = json.loads((FRONTEND_DIR / ".lintstagedrc.json").read_text(encoding="utf-8"))
        commands = " ".join(cmd for cmds in data.values() for cmd in cmds)
        assert "eslint --config eslint.config.js" in commands
