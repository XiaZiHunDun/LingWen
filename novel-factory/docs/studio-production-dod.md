# Studio 真实生产 · 完成定义（DoD）

> **版本**：production-dod-v2.1 · 2026-06-22  
> **状态**：A–E 已绿（本地 DoD + CI `67c8ad8`）
> **用途**：验证「灵文工作室」在 **临时新书** 上能跑通真实 MiniMax 生产（单章 + 三章 batch）。

---

## 范围

| 包含 | 不包含 |
|------|--------|
| 临时项目 **1 章** / **3 章 batch** 真实 LLM | 七样章 prose polish |
| preflight → pilot/batch → emit → full-check | 星陨 wave 367–376（runbook §18） |
| 记录写入 `infra/.state/pilot_records/` | SaaS 部署 |

---

## DoD 清单

### A–B. 环境 + 脚手架（无 API）✅

- [x] `python lingwen.py doctor`（`verify-studio-production-dod.sh` 无 API 路径）
- [x] preflight-only + `verify-onboarding.sh ci-smoke`

### C. 真实 LLM **单章** ✅（2026-06-22 本地绿 · ~$0.036）

```bash
bash scripts/verify-studio-production-dod.sh --real-llm
```

### D. 真实 LLM **batch 三章** ✅（2026-06-22 · 3/3 emit · ~$0.19 · 无 P0）

```bash
bash scripts/verify-studio-production-dod.sh --real-llm-batch
# 可选：--batch-budget 0.50（须配合 --calibrate-from 或自动选最新 studio-dod-batch*.json）
# F79 默认 ~$0.028/章 · Studio MiniMax 实测 ~$0.063/章；无 cap 时默认不设 budget
```

- [x] `chapters_succeeded == 3` · batch summary 在 `pilot_records/`
- [x] `lingwen.py check 1-3 --full --fail-severity P0` 无 P0

### E. CI 对齐 ✅（2026-06-22）

- [x] GitHub **test** workflow 全绿 — run [`27928469270`](https://github.com/XiaZiHunDun/LingWen/actions/runs/27928469270) · `67c8ad8`
- [x] llm×7 **路径过滤**（纯文档 push 跳过；改样章/infra 或 label `llm-check` 时跑）

---

## 一键命令

```bash
cd novel-factory
bash scripts/verify-studio-production-dod.sh              # A+B（无 API）
bash scripts/verify-studio-production-dod.sh --real-llm     # + C
bash scripts/verify-studio-production-dod.sh --real-llm-batch  # + D
```

临时项目 `projects/studio-dod-*` 退出时删除；记录保留在 gitignored `pilot_records/`。

---

## 对外 dist

七样章默认 zip：

```bash
bash scripts/prepare-studio-samples-zip.sh
# → dist/灵文工作室-七样章.zip
```

索引：[`trial-read-index.md`](trial-read-index.md)

---

## 文档索引

- [`chapter-production-runbook.md`](chapter-production-runbook.md)
- [`ci-quality-gates.md`](ci-quality-gates.md)
