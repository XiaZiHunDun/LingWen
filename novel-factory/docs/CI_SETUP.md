# CI Setup Guide (Phase 8.3)

> **目的**: Real LLM tests 在 GitHub Actions 定时跑, 抓 production 路径 regression 24h 内.

## 概述

- **Workflow**: `.github/workflows/real-llm-tests.yml`
- **Trigger**: 每天 UTC 02:00 (北京时间 10:00) + 手动 workflow_dispatch
- **Provider**: Anthropic only (Phase 8 HAIKU, ~$0.025/run)
- **月成本估算**: $0.75 (30 daily runs)

## 步骤 1: 添加 `ANTHROPIC_API_KEY` secret

GitHub UI 操作:

1. 打开 https://github.com/XiaZiHunDun/LingWen/settings/secrets/actions
2. 点击 **New repository secret**
3. 填写:
   - **Name**: `ANTHROPIC_API_KEY`
   - **Secret**: `sk-ant-...` (主公自己的 Anthropic API key)
4. 点击 **Add secret**

## 步骤 2: 验证 workflow 跑通 (手动 dispatch)

GitHub UI 操作:

1. 打开 https://github.com/XiaZiHunDun/LingWen/actions/workflows/real-llm-tests.yml
2. 点击 **Run workflow** → 选 master branch → **Run workflow**
3. 等待 ~30-60s (TestNovelWritingRealLLM 6 LLM calls) + ~5-10s (TestPolishMergeSynthesisRealLLM 1 LLM call)
4. 检查 job 状态:
   - ✅ Green check = 2 passed, 0 failed
   - ❌ Red X = 看 log troubleshooting (见下方)

期望 pytest 输出:

```
tests/agent_system/test_novel_writing_real_llm.py::TestNovelWritingRealLLM::test_novel_writing_yaml_polish_merge_produces_s1_s8_scores PASSED
tests/agent_system/test_novel_writing_real_llm.py::TestPolishMergeSynthesisRealLLM::test_polish_merge_synthesis_with_distinct_contents PASSED
======================== 2 passed, 2 skipped in 45.32s ========================
```

(2 skipped 是 OpenAI/MiniMax 测试, 无 key 默认 SKIP, 符合预期)

## 步骤 3: 验证 cron 触发 (24h 后)

1. 打开 https://github.com/XiaZiHunDun/LingWen/actions
2. 找到带 **scheduled** 标签的 run
3. 期望: 跟 manual dispatch 一样 pass

## 步骤 4: 验证 secret 不泄漏 (sanity check)

1. 打开任一 workflow run → 点 job → 查看 log
2. 搜 "ANTHROPIC" → 应该看到 `***` (GitHub 自动 redact)
3. pytest output 不含明文 key

## 失败 troubleshooting

| 失败原因 | 解决 |
|----------|------|
| `ANTHROPIC_API_KEY secret is not set` | 步骤 1 没做 / secret 名拼错, 去 Settings → Secrets 检查 |
| `401 Unauthorized` | API key 过期或失效, 重新生成并更新 secret |
| `Timeout` / `Rate limit` | Anthropic 服务问题, 等几分钟重 dispatch |
| 真实 LLM 输出格式变化 (HAIKU 不输出 `scores_{label}` 格式) | Phase 8.1 robustness 没覆盖, 修 `_parse_merge_response` 或 prompt (master_controller.py) |
| Phase 7.5/8.1 代码 regression | 查 master_controller.py / prompts.py diff, 找最近改动, revert 验证 |

## 禁用 workflow

**临时禁用** (推荐):

GitHub UI → Actions → Real LLM Tests → ... → **Disable workflow**

**永久禁用** (改 cron 注释):

```bash
# 编辑 .github/workflows/real-llm-tests.yml, 改:
#   schedule:
#     - cron: '0 2 * * *'
# 为:
#   # schedule:  # disabled YYYY-MM-DD
#   #   - cron: '0 2 * * *'
git add .github/workflows/real-llm-tests.yml
git commit -m "ci: disable real-llm-tests cron (reason)"
```

## 成本监控

- GitHub billing: https://github.com/settings/billing (看 Actions minutes)
- Anthropic usage: https://console.anthropic.com/settings/usage
- 单 run 估算: ~$0.025 (HAIKU 6 calls + Sonnet 1 call)
- 每天 1 次: ~$0.75/月
- 手动 dispatch × N: 叠加

## 安全注意

- **不要**把 `ANTHROPIC_API_KEY` commit 到任何文件
- **不要**在 PR 评论 / issue / public log 暴露
- GitHub secrets 自动 redact, 但还是要小心 `${{ secrets.XXX }}` 的输出
- 定期 rotate (Anthropic 建议 90 天)
