# Studio 真实生产 · 完成定义（DoD）

> **版本**：production-dod-v1 · 2026-06-22  
> **用途**：判断「灵文工作室」是否能在 **新书** 上完成 **1 章真实 MiniMax 生产**，而非仅依赖已修定的七样章 dist。

---

## 范围

| 包含 | 不包含 |
|------|--------|
| 新书或 test 项目 1 章 **真实 LLM** pilot | 七样章 prose polish（见 [`prose-rubric-v2.md`](prose-rubric-v2.md)） |
| preflight → pilot/batch → emit → full-check | 星陨 364+ 批量续跑（见 runbook §17–18） |
| Dashboard / 生产记录可核对 | SaaS 部署 |

---

## DoD 清单（全部 ✅ = 生产链路可用）

### A. 环境与密钥

- [ ] `python lingwen.py doctor` 通过
- [ ] `MINIMAX_API_KEY` 已配置（本地 `.env` 或 CI Secret）
- [ ] `LINGWEN_PROJECT_ROOT` 指向目标 `projects/<slug>`

### B. 脚手架（无 LLM）

- [ ] `python -m infra.agent_system.chapter_production_pilot --preflight-only --chapter-num 1` 通过
- [ ] `bash scripts/verify-onboarding.sh ci-smoke` 通过（可选 · 与 CI 对齐）

### C. 真实 LLM 单章（核心）

- [ ] 跑通 **1 章** 真实写作（任选其一）：

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/<slug>"
export MINIMAX_API_KEY=...

# 方式 1：pilot 单章（需 LINGWEN_REAL_LLM=1）
export LINGWEN_REAL_LLM=1
python -m infra.agent_system.chapter_production_pilot --chapter-num 1

# 方式 2：workflow 单章（与 agent E2E 同路径）
pytest tests/agent_system/test_novel_writing_real_llm.py -k MiniMax -v
```

- [ ] 产出章节文件写入 `03_内容仓库/`（或项目约定路径）
- [ ] `python lingwen.py check 1 --full --fail-severity P0` 通过（或等价 full-check）

### D. 可观测性

- [ ] Dashboard 可看到该次 run / 决策 / 成本（若启用 dashboard）
- [ ] 或本地 `production_summary` / batch record 可核对（见 runbook）

### E. CI 对齐（工程侧）

- [ ] GitHub **`test` workflow** 全绿（含 llm-golden · e2e-live）
- [ ] 可选：Actions → **real-llm-tests** 手动绿（MiniMax agent 3 tests）

---

## 一键自检（本地）

```bash
cd novel-factory
bash scripts/verify-studio-production-dod.sh                 # A+B+E（无 API）
bash scripts/verify-studio-production-dod.sh --real-llm      # 含 DoD C（MiniMax · 临时项目 · 自动清理）
bash scripts/verify-studio-production-dod.sh --from-verify   # 含 e2e-live 本地模拟
```

**DoD C** 会在 `projects/studio-dod-<timestamp>/` 跑 1 章真实 pilot，记录写入 `infra/.state/pilot_records/studio-dod-*.json`（gitignored），项目目录退出时删除。

---

## 与七样章 dist 的关系

| 维度 | 七样章 dist | Studio 生产 DoD |
|------|-------------|-----------------|
| 目的 | 对外样章 · prose 4.0+ | 验证 **可复制生产** |
| 验收 | `run-primary-revision-verify.sh` | 本文 + pilot 1 章 |
| CI | llm-golden-primary ×7 blocking | real-llm-tests 手动 |

七样章齐平 **不替代** 新书 pilot；发新书前仍建议跑通 DoD C 段。

---

## 文档索引

- 生产细节：[`chapter-production-runbook.md`](chapter-production-runbook.md)
- Onboarding：[`studio-onboarding.md`](studio-onboarding.md)
- CI：[`ci-quality-gates.md`](ci-quality-gates.md)
