# Review Modes — Full / Lean / Solo

> Adapted from CCGS's review intensity pattern.

## Overview

Three configurable review intensities allow the novel factory to balance quality rigor against throughput speed based on project phase and resource availability.

## Mode Comparison

| Aspect | Full | Lean | Solo |
|--------|------|------|------|
| **Quality bar** | S级 (≥90%) | A级 (≥70%) | B级 (≥50%) |
| **Reviewers** | 10 concurrent | 5 concurrent | Self only |
| **Dimensions** | 10+1 (all) | 6 (key rules) | 2 (basic) |
| **LLM-based checks** | Yes (character_arc) | No | No |
| **Max iterations** | 3 | 2 | 1 |
| **Throughput** | Slowest | Balanced | Fastest |
| **Use when** | Final quality gate, major release | Batch review, iterative improvement | Early drafts, self-check |

## Dimension Mapping by Mode

| Dimension | Full | Lean | Solo |
|-----------|------|------|------|
| naming_consistency | ✅ | ✅ | ✅ |
| content_integrity | ✅ | ✅ | ✅ |
| chapter_repeat | ✅ | ✅ | ❌ |
| character_state | ✅ | ✅ | ❌ |
| timeline | ✅ | ❌ | ❌ |
| plot_relevance | ✅ | ✅ | ❌ |
| foreshadow_tracking | ✅ | ❌ | ❌ |
| scene_logic | ✅ | ✅ | ❌ |
| emotional_rhythm | ✅ | ❌ | ❌ |
| dialogue_style | ✅ | ❌ | ❌ |
| character_arc (LLM) | ✅ | ❌ | ❌ |

## When to Use Each Mode

### Full Review (Default)
- Major milestones: volume finals, novel completion
- High-stakes chapters: climaxes, emotional peaks
- When quality is non-negotiable (e.g., publication-ready)
- Resource cost: ~$15-30 per 10-chapter batch

### Lean Review
- Regular batch reviews (weekly cycles)
- When time-to-market matters more than perfection
- Mid-project iteration tracking
- Resource cost: ~$5-10 per 10-chapter batch

### Solo Review
- First draft self-check before submission
- When writer wants a quick sanity check
- Exploratory chapters with high revision probability
- Resource cost: ~$0.50 per 10-chapter batch

## Switching Modes

```bash
# Switch to lean mode for faster iteration
REVIEW_MODE=lean ./run_review.sh batch ch101-ch110

# Check current mode
cat novel-factory/workflow_state.json | grep active_review_mode

# Mode is persisted per workflow state
```

## Mode Transition Rules

| Transition | Allowed? | Notes |
|------------|----------|-------|
| solo → lean | ✅ | After self-check passes |
| lean → full | ✅ | After lean review reveals issues |
| full → lean | ✅ | After critical path stabilized |
| lean → solo | ❌ | Cannot skip human review entirely |
| solo → full | ✅ | Jump to highest rigor anytime |

---

*Document version: v1.0*
*Adapted from CCGS review modes*
*Created: 2026-05-19*