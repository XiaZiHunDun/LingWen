# LLM Provider Benchmark — 2026-08-26-baseline

## Run
- run_id: `2026-08-26-baseline`
- providers: minimax
- calls/provider: 10
- fixture: huiyu-dangan/golden-set/chapters/{ch001, ch003, ch010} + 林栀

## Per-provider metrics

| provider | parse_rate | schema_compliance | canon_level | composite | cost/call | p50 (s) | p95 (s) | consistency |
|----------|-----------|------------------|-------------|-----------|-----------|---------|---------|-------------|
| minimax | 0.20 | 1.00 | 1.00 | 0.73 | $0.0004 | 4.98 | 9.52 | 1.00 |

## Confidence distribution

| provider | high | medium | low |
|----------|------|--------|-----|
| minimax | 0 | 0 | 0 |

## Threshold check

Quality threshold = 0.90.

Providers below threshold (composite-desc):
1. minimax (composite=0.73, cost=$0.0004, parse_rate=0.20)

## Recommended priority

```python
default_priority = ["minimax"]
```

Reasoning: above-threshold providers ordered by cost asc; below-threshold appended.
