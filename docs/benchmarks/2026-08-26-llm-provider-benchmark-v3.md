# LLM Provider Benchmark — 2026-08-26-v3

## Run
- run_id: `2026-08-26-v3`
- providers: minimax
- calls/provider: 10
- fixture: huiyu-dangan/golden-set/chapters/{ch001, ch003, ch010} + 林栀

## Per-provider metrics

| provider | parse_rate | schema_compliance | canon_level | composite | cost/call | p50 (s) | p95 (s) | consistency |
|----------|-----------|------------------|-------------|-----------|-----------|---------|---------|-------------|
| minimax | 0.60 | 1.00 | 1.00 | 0.87 | $0.0006 | 3.61 | 5.05 | 0.33 |

## Confidence distribution

| provider | high | medium | low |
|----------|------|--------|-----|
| minimax | 0 | 0 | 0 |

## Threshold check

Quality threshold = 0.90.

Providers below threshold (composite-desc):
1. minimax (composite=0.87, cost=$0.0006, parse_rate=0.60)

## Recommended priority

```python
default_priority = ["minimax"]
```

Reasoning: above-threshold providers ordered by cost asc; below-threshold appended.
