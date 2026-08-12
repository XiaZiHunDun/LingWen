# lingwen-llm

LingWen · LLM Provider 抽象层。

支持的 provider: OpenAI / Anthropic / MiniMax / 自定义 router。

## 安装

```bash
pip install -e ".[test]"
```

## 测试

```bash
pytest -q
```

## 来源

原 `infra/ai_service/`，2026-08 由 Phase 17.5 迁入，迁入路径 `lingwen_llm.providers/`。
