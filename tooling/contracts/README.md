# tooling/contracts

Codegen + reverse-validation tooling for lingwen-shared.

## generate.py

Reads `packages/lingwen-shared/src/lingwen_shared/contracts/python/*.py`,
emits `packages/lingwen-shared/src/lingwen_shared/contracts/ts/*.ts`.

```bash
uv run python tooling/contracts/generate.py
```

Uses Pydantic v2's `model_json_schema()` directly + a hand-rolled JSON Schema → TS
converter. Hand-rolled approach avoids `pydantic-to-typescript` library version
drift; sufficient for v16.1's 12 DTO starter set.

## zod_revalidate.py (T5)

Reads FastAPI OpenAPI schema (from running server or static dump),
emits zod schemas, diffs against `contracts/ts/*.ts`.

```bash
uv run python tooling/contracts/zod_revalidate.py --base-url http://localhost:8765
```

## CI gate

The `zod_revalidate.py` runs in a separate CI job (per Q5=B decision).
Dev loop is not blocked by zod checks.