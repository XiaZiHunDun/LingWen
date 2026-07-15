#!/usr/bin/env python3
"""
Phase B: Batch-migrate checker classes to use Registry pattern.

For each unique CheckerType class:
1. Insert `_checker_type = CheckerType.XXX` after class declaration
2. Replace `super().__init__(CheckerType.XXX)` with `super().__init__(self._checker_type)`

Skips 3 conflict classes (CoreForeshadow/CoreProps/DialogueAuthenticity) - handled in Phase C.
"""
import re
import sys
from pathlib import Path

CHECKERS_DIR = Path("infra/consistency/checkers")

# 26 unique CheckerType mappings: (class_name_in_file, CheckerType.ENUM_VALUE)
# Derived from grep of super().__init__ calls
MIGRATIONS = [
    ("ability_checker.py", "AbilityChecker", "ABILITY"),
    ("ai_gloss_checker.py", "AIGlossChecker", "AI_GLOSS"),
    ("battle_visualization.py", "BattleVisualizationChecker", "BATTLE_VISUALIZATION"),
    ("causal_chain_checker.py", "CausalChainChecker", "CAUSAL_CHAIN"),
    ("chapter_redundancy_checker.py", "ChapterRedundancyChecker", "CHAPTER_REDUNDANCY"),
    ("character_agency.py", "CharacterAgencyChecker", "CHARACTER_AGENCY"),
    ("character_checker.py", "CharacterChecker", "CHARACTER"),
    ("character_state.py", "CharacterStateChecker", "CHARACTER_STATE"),
    ("cross_chapter_logic_checker.py", "CrossChapterLogicChecker", "CROSS_CHAPTER_LOGIC"),
    ("dialogue_action_checker.py", "DialogueActionChecker", "DIALOGUE_ACTION"),
    ("foreshadow_checker.py", "ForeshadowChecker", "FORESHADOW"),
    ("foreshadow_quality.py", "ForeshadowQualityChecker", "FORESHADOW_QUALITY"),
    ("gender_consistency_checker.py", "GenderConsistencyChecker", "GENDER_CONSISTENCY"),
    ("item_checker.py", "ItemChecker", "ITEM"),
    ("llm_causal_reasoning_checker.py", "LLMCausalReasoningChecker", "LLM_CAUSAL_REASONING"),
    ("narrative_perspective_checker.py", "NarrativePerspectiveChecker", "NARRATIVE_PERSPECTIVE"),
    ("outline_checker.py", "OutlineChecker", "OUTLINE"),
    ("pacing_checker.py", "PacingChecker", "PACING"),
    ("personality_checker.py", "PersonalityChecker", "PERSONALITY"),
    ("relationship_state_checker.py", "RelationshipStateChecker", "RELATIONSHIP_STATE"),
    ("repair_trace_checker.py", "RepairTraceChecker", "REPAIR_TRACE"),
    ("repetitive_phrase_checker.py", "RepetitivePhraseChecker", "REPETITIVE_PHRASE"),
    ("scene_pattern_repeat.py", "ScenePatternRepeatChecker", "SCENE_PATTERN"),
    ("scene_transition_checker.py", "SceneTransitionChecker", "SCENE_TRANSITION"),
    ("sentence_diversity_checker.py", "SentenceDiversityChecker", "SENTENCE_DIVERSITY"),
    ("spatial_transition_checker.py", "SpatialTransitionChecker", "SPATIAL_TRANSITION"),
    ("timeline_age.py", "TimelineAgeConsistencyChecker", "TIMELINE_AGE"),
    ("timeline_checker.py", "TimelineChecker", "TIMELINE"),
]

CLASS_DEF_RE = re.compile(
    r'^(class\s+{class_name}\s*\(\s*BaseChecker\s*\):.*?)([\s\S]*?)(def\s+__init__\s*\([^)]*\)\s*->?\s*[^{]*:)',
    re.MULTILINE,
)


def migrate_one(filename: str, class_name: str, enum_value: str) -> tuple[bool, str]:
    """Migrate a single checker file. Returns (changed, message)."""
    filepath = CHECKERS_DIR / filename
    if not filepath.exists():
        return False, f"NOT FOUND: {filepath}"

    original = filepath.read_text(encoding="utf-8")

    # Idempotency check: if _checker_type already present, skip
    if f"_checker_type = CheckerType.{enum_value}" in original:
        return False, f"ALREADY MIGRATED: {filename}"

    # Step 1: Find the class declaration line and insert _checker_type after it
    # Match `class XxxChecker(BaseChecker):` with optional docstring
    class_pattern = re.compile(
        rf'^class\s+{re.escape(class_name)}\s*\(\s*BaseChecker\s*\)\s*:\s*$',
        re.MULTILINE,
    )
    m = class_pattern.search(original)
    if not m:
        return False, f"CLASS NOT FOUND: {class_name} in {filename}"

    # Determine what's after the class line: docstring or __init__
    # We insert `_checker_type = CheckerType.XXX` after the class line + docstring
    # Simple heuristic: find the class line, then look at the next non-blank lines
    class_line_end = m.end()
    after = original[class_line_end:]

    # Check if there's a docstring (triple-quoted string) right after class line
    docstring_match = re.match(
        r'(\s*"""[\s\S]*?""")',
        after,
    )
    if docstring_match:
        insert_pos = class_line_end + docstring_match.end()
    else:
        # No docstring - insert right after the class line
        insert_pos = class_line_end

    # Step 2: Insert `_checker_type = CheckerType.XXX` line
    new_text = (
        original[:insert_pos]
        + f"\n    _checker_type = CheckerType.{enum_value}\n"
        + original[insert_pos:]
    )

    # Step 3: Replace super().__init__(CheckerType.XXX) with super().__init__(self._checker_type)
    new_text = new_text.replace(
        f"super().__init__(CheckerType.{enum_value})",
        "super().__init__(self._checker_type)",
    )

    if new_text == original:
        return False, f"NO CHANGES: {filename}"

    filepath.write_text(new_text, encoding="utf-8")
    return True, f"MIGRATED: {filename} ({class_name} -> CheckerType.{enum_value})"


def main():
    changed = 0
    skipped = 0
    errors = []
    for filename, class_name, enum_value in MIGRATIONS:
        try:
            ok, msg = migrate_one(filename, class_name, enum_value)
            if ok:
                changed += 1
            else:
                skipped += 1
            print(msg)
        except Exception as e:
            errors.append((filename, str(e)))
            print(f"ERROR: {filename}: {e}", file=sys.stderr)

    print()
    print(f"Summary: {changed} changed, {skipped} skipped, {len(errors)} errors")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
