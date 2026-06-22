"""Phase 12.11: Studio samples zip defaults to seven books."""
from __future__ import annotations

from pathlib import Path

NOVEL_FACTORY = Path(__file__).resolve().parents[2]


class TestStudioSamplesZip1211:
    def test_prepare_script_defaults_to_seven(self):
        text = (NOVEL_FACTORY / "scripts" / "prepare-studio-samples-zip.sh").read_text(
            encoding="utf-8",
        )
        assert 'STUDIO_SAMPLES="${STUDIO_SAMPLES:-7}"' in text
        assert "灵文工作室-七样章.zip" in text
        assert "huangsha-dangan" in text
        assert "anhe-dangan" in text
