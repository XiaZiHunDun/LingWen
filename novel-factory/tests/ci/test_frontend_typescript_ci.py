"""Phase 9.49 F38: TypeScript strict full rollout contract tests."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = REPO_ROOT / "novel-factory" / "dashboard" / "frontend"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "dashboard-frontend-ci.yml"


class TestFrontendTypescriptStrict:
    def test_tsconfig_strict_allow_js(self):
        cfg = json.loads((FRONTEND_DIR / "tsconfig.json").read_text(encoding="utf-8"))
        opts = cfg["compilerOptions"]
        assert opts["strict"] is True
        assert opts["allowJs"] is True
        assert opts["noEmit"] is True

    def test_package_has_typecheck_script_and_typescript(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        assert pkg["scripts"]["typecheck"] == "tsc -p tsconfig.json --noEmit"
        assert "typescript" in pkg.get("devDependencies", {})

    def test_tsconfig_includes_all_unit_specs(self):
        cfg = json.loads((FRONTEND_DIR / "tsconfig.json").read_text(encoding="utf-8"))
        includes = cfg.get("include", [])
        assert "tests/unit/**/*.ts" in includes
        excludes = " ".join(cfg.get("exclude", []))
        assert "fixtures" in excludes

    def test_unit_spec_ts_files_at_least_thirty(self):
        unit = FRONTEND_DIR / "tests" / "unit"
        ts_specs = list(unit.glob("*.spec.ts"))
        assert len(ts_specs) >= 30

    def test_ci_workflow_runs_typecheck(self):
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "pnpm typecheck" in text

    def test_package_has_typecheck_app_script_and_vue_tsc(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        assert pkg["scripts"]["typecheck:app"] == "vue-tsc -p tsconfig.app.json --noEmit"
        assert "vue-tsc" in pkg.get("devDependencies", {})

    def test_tsconfig_app_includes_src_vue(self):
        cfg = json.loads((FRONTEND_DIR / "tsconfig.app.json").read_text(encoding="utf-8"))
        includes = cfg.get("include", [])
        assert any("src/**/*.vue" in p for p in includes)
        assert cfg["compilerOptions"]["strict"] is True

    def test_ci_workflow_runs_typecheck_app(self):
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "pnpm typecheck:app" in text
