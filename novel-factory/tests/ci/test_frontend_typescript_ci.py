"""Phase 9.40 F25: TypeScript strict pilot contract tests."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = REPO_ROOT / "novel-factory" / "dashboard" / "frontend"
PILOT_TS_SPECS = [
    "ripple-card.spec.ts",
    "ripple-filter.spec.ts",
    "cascade-graph.spec.ts",
    "useWorkflowSocket.spec.ts",
    "use-tier-budget-alerts.spec.ts",
]


class TestFrontendTypescriptStrict:
    def test_tsconfig_strict_allow_js(self):
        import json as json_mod

        cfg = json_mod.loads((FRONTEND_DIR / "tsconfig.json").read_text(encoding="utf-8"))
        opts = cfg["compilerOptions"]
        assert opts["strict"] is True
        assert opts["allowJs"] is True
        assert opts["noEmit"] is True

    def test_package_has_typecheck_script_and_typescript(self):
        pkg = json.loads((FRONTEND_DIR / "package.json").read_text(encoding="utf-8"))
        assert pkg["scripts"]["typecheck"] == "tsc -p tsconfig.json --noEmit"
        assert "typescript" in pkg.get("devDependencies", {})

    def test_pilot_specs_migrated_to_ts(self):
        unit = FRONTEND_DIR / "tests" / "unit"
        for name in PILOT_TS_SPECS:
            assert (unit / name).is_file(), name
            assert not (unit / name.replace(".ts", ".js")).exists(), name

    def test_pilot_spec_count_at_least_five(self):
        assert len(PILOT_TS_SPECS) >= 5
