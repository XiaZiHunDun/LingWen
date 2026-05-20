# tools/consistency vs consistency/checkers/ Audit Report

**Date**: 2026-05-20
**Auditor**: Claude Code
**Base Path**: `/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory`

---

## Summary

| Category | Count |
|----------|-------|
| Total function-based checkers in `tools/consistency/` | 16 |
| Total class-based checkers in `consistency/checkers/` | 10 |
| Duplicates (function≈class) | 3 |
| Unique function-based functionality | 13 |
| Candidates for deprecation | 3 |

---

## Detailed Analysis

### 1. Duplicate / Migrated Checkers

These function-based checkers have equivalent class-based implementations. The class-based versions are the **canonical implementations**.

| Checker | Type | Purpose | Equivalent in consistency/checkers | Status |
|---------|------|---------|-----------------------------------|--------|
| `check_character_state.py` | function | Character alive/dead, gender consistency | `character_state.py` (class) | **DUPLICATE** - Class version is canonical |
| `check_timeline.py` | function | Timeline anomaly detection (instant vs past keywords) | `timeline_checker.py` (class) | **DUPLICATE** - Class version is canonical |
| `check_naming.py` | function | Chapter filename vs title number matching | `naming.py` (class) | **DUPLICATE** - Class version is canonical |

### 2. Partially Overlapping Checkers

| Checker | Type | Purpose | Overlap | Status |
|---------|------|---------|---------|--------|
| `check_plot_device_tracking.py` | function (class-like) | Foreshadowing tracker with PlotDeviceTracker class | `foreshadow_checker.py` | **PARTIAL OVERLAP** - `plot_device_tracking.py` is more sophisticated (tier-based windows, workorder generation); `foreshadow_checker.py` is more structured but less feature-rich |

### 3. Unique Function-Based Checkers (No Class Equivalent)

These checkers in `tools/consistency/` provide **unique functionality** not present in `consistency/checkers/`:

| Checker | Type | Purpose | Assessment |
|---------|------|---------|------------|
| `check_battle_density.py` | function | Battle scene density with wartime/peacetime classification | **UNIQUE** - Sophisticated 3-tier keyword system |
| `check_character_activity.py` | function | Character "tool person" detection, proactive vs passive scoring, relationship tightness | **UNIQUE** - Novel concept of detecting "工具人" characters |
| `check_character_arc_llm.py` | function (helper) | Generates prompts for LLM-based character arc analysis | **UNIQUE** - Orchestrates LLM analysis, not a direct checker |
| `check_dialogue_style.py` | function (class-like) | Dialogue style consistency with character voice profiles | **UNIQUE** - Character voice fingerprinting |
| `check_duplicate.py` | function | Cross-chapter text similarity detection | **UNIQUE** - difflib-based similarity |
| `check_emotional_rhythm.py` | function (class-like) | Emotional rhythm health with shift detection | **UNIQUE** - Emotion word banking with balance calculation |
| `check_faction_relations.py` | function | Faction relationship tracking (ALLIED/HOSTILE/BETRAY) | **UNIQUE** - Faction graph tracking |
| `check_realm_system.py` | function | Cultivation realm system consistency (粒子境→创世境) | **UNIQUE** - 9-tier realm hierarchy with promotion detection |
| `check_scene_density.py` | function | Scene type classification (combat/emotional/info/narrative) | **UNIQUE** - Rule-based scene classifier with subdimensions |
| `check_scene_logic.py` | function (class-like) | Scene continuity between chapters (location/character overlap) | **UNIQUE** - Cross-chapter similarity scoring |
| `check_segment_relevance.py` | function (class-like) | Paragraph relevance to surrounding chapters | **UNIQUE** - Sliding window keyword correlation |
| `check_template_sentences.py` | function | Template sentence repetition with workorder generation | **UNIQUE** - N-gram detection + synonym suggestions |

### 4. Utility/Runner Files

| File | Purpose | Assessment |
|------|---------|------------|
| `base_checker.py` (tools/consistency) | Base class for function-based checkers | **UTILITY** - Provides common report formatting |
| `auto_consistency_checker.py` | Auto-detects issues using class-based engine | **RUNNER** - Uses consistency/checkers/ classes |
| `run_quality_checks.py` | CLI runner for quality checks | **RUNNER** - Uses function-based checkers |
| `run_unified_quality.py` | Unified quality runner | **RUNNER** - Aggregation script |
| `integrity_checker.py` | Island chapter detection | **UTILITY** - Helper for finding isolated chapters |
| `fix_naming.py`, `fix_island_chapters_v2.py` | Fix scripts | **FIXERS** - Not checkers |
| `quality_engine.py` | Quality gate engine | **ENGINE** - Works with class-based system |
| `template_synonyms.yaml` | Synonym dictionary for template detector | **DATA** - Used by check_template_sentences.py |

---

## Recommendations

### Candidates for Deprecation (3 files)

These function-based checkers are strictly worse than their class-based counterparts:

| File | Reason |
|------|--------|
| `check_character_state.py` | Duplicated by `consistency/checkers/character_state.py` which has proper Issue dataclass, severity levels, and context-aware checking |
| `check_timeline.py` | Duplicated by `consistency/checkers/timeline_checker.py` which has structured TimelinePoint dataclass and timeline history tracking |
| `check_naming.py` | Duplicated by `consistency/checkers/naming.py` - both are simple but class version is canonical |

**Action**: Deprecate these 3 files after confirming class-based versions pass all existing tests.

### Keep but Consider Integration (13 files)

These provide **unique or more sophisticated functionality** not in the class-based system:

1. **check_battle_density.py** - Battle density detection is genre-specific; keep as specialized tool
2. **check_character_activity.py** - "Tool person" detection is innovative; consider extracting as a skill
3. **check_character_arc_llm.py** - LLM orchestration helper; unique approach
4. **check_dialogue_style.py** - Character voice fingerprinting; sophisticated
5. **check_duplicate.py** - Cross-chapter similarity; not covered by class system
6. **check_emotional_rhythm.py** - Emotion banking; sophisticated analysis
7. **check_faction_relations.py** - Faction graph; unique tracking
8. **check_realm_system.py** - Cultivation levels; genre-specific
9. **check_scene_density.py** - Scene classification; sophisticated
10. **check_scene_logic.py** - Continuity scoring; useful
11. **check_segment_relevance.py** - Paragraph relevance; useful
12. **check_template_sentences.py** - Template detection; mature with workorders

### Partial Overlap (1 file)

| File | Recommendation |
|------|----------------|
| `check_plot_device_tracking.py` | **Keep separately** - `PlotDeviceTracker` class is more sophisticated than `ForeshadowChecker` with tier-based windows (core/normal/edge), workorder generation, and fuzzy matching. Consider merging best features. |

---

## Architecture Notes

### Function-Based System (tools/consistency/)

- **Pattern**: Standalone Python scripts with `check_*` functions
- **Output**: Text reports to stdout/files
- **State**: No persistent state between runs (hardcoded character lists)
- **Strengths**: Self-contained, easy to run individually, rich domain logic

### Class-Based System (consistency/checkers/)

- **Pattern**: Extends `BaseChecker` abstract class
- **Output**: Structured `Issue` dataclass with severity, location, evidence
- **State**: Maintains history across chapters (character_state, timeline, etc.)
- **Strengths**: Composable, integrates with `ConsistencyEngine`, reusable

---

## Test Verification

Run the following to verify nothing broke:
```bash
python3 -m pytest tests/consistency/ -x -q --tb=short
```

---

## Conclusion

The `tools/consistency/` directory contains **mature, sophisticated domain-specific checkers** that are largely **not duplicated** in the class-based `consistency/checkers/` system. Only **3 files** (character_state, timeline, naming) are strict duplicates suitable for deprecation.

The majority of function-based checkers implement **unique quality dimensions** (battle density, emotional rhythm, faction relations, template detection, etc.) that the class-based system does not cover.

**Recommended Action**: Keep 13 unique checkers as-is. Deprecate 3 duplicates after verification.
