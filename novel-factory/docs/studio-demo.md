# 灵文工作室 · 产品 Demo 脚本

> **版本**：demo-v2 · 2026-06-20  
> **时长**：15 分钟（快览）/ 30 分钟（完整）  
> **受众**：编辑、合作方、内测读者、工程验收

---

## Demo 目标（一句话）

**灵文工作室 = 可复用的小说生产系统**：30 分钟从零脚手架到试读包 + 质检报告，**八本项目**（七书 Studio + 星陨 testbed）验证可复制；**对外主打样章** = [`静海日志`](../projects/jinghai-rizhi/docs/trial-read-ch001-003.md)。

---

## 准备（Demo 前 5 分钟）

```bash
cd novel-factory
cp .env.example .env          # 可选：真实 pilot 需 MINIMAX_API_KEY
python lingwen.py doctor
```

打开本地文件（无需启动服务也可完成前半段）：

| 文件 | 用途 |
|------|------|
| [`docs/trial-read-index.md`](trial-read-index.md) | 八书 + 星陨试读入口 |
| [`projects/jinghai-rizhi/docs/trial-read-ch001-003.md`](../projects/jinghai-rizhi/docs/trial-read-ch001-003.md) | **主打样章**开篇 3 章 |
| [`projects/huiyu-dangan/docs/trial-read-ch001-003.md`](../projects/huiyu-dangan/docs/trial-read-ch001-003.md) | 灰域档案开篇 |
| [`projects/anye-xinbiao/docs/trial-read-ch001-003.md`](../projects/anye-xinbiao/docs/trial-read-ch001-003.md) | 暗夜信标开篇 |

---

## 路线 A · 15 分钟快览（无 LLM）

### 1. 产品定位（2 分钟）

- **不是**无止尽续写《星陨》——星陨 = testbed（360 章正史 + stress test）
- **是** Studio：init → preflight → batch → check → 试读包
- 成功指标：**八项目 10 章闭环**（七书 Studio + 星陨 testbed），而非章数 KPI

### 2. 试读分发（5 分钟）

打开 [`trial-read-index.md`](trial-read-index.md)，**先展示主打样章**：

1. **《静海日志》** ch001 雾港·频道十七（**对外样章定稿**）
2. **《灰域档案》** ch001：「你看到了。」
3. **《暗夜信标》** ch001 信标脉冲
4. **《雪线档案》** ch001 封山·频道 9
5. （可选）**《星陨纪元》** testbed 开篇 3 章

强调：Studio 七书 + 星陨 **P0=0**，Golden Set CI matrix **八 slug**。

### 3. 工程可复制（5 分钟）

```bash
bash scripts/verify-studio-release.sh
# 或仅 onboarding 盲测：
bash scripts/verify-onboarding-blind.sh
```

讲解：init → preflight → dry-run batch → **项目级角色表**（不误报星陨角色）。

### 4. 收尾（3 分钟）

- CI：`golden-set` matrix（**八 slug**）+ `onboarding-smoke`
- 下一本：改大纲 + pillars → 同样流程

---

## 路线 B · 30 分钟完整（含 Dashboard）

> **录屏分镜稿**：[`studio-demo-recording-script.md`](studio-demo-recording-script.md)（时间轴 + 话术 + 镜头）

在路线 A 基础上增加：

### 5. 启动 Dashboard（3 分钟）

```bash
# 单端口（推荐：Cursor SSH 远程开发）
bash scripts/run-dashboard-single-port.sh
```

浏览器：**`http://127.0.0.1:8765/?nav=studio`**

Cursor SSH：先在 IDE 内点击 Ports 里的 8765 链接激活转发，再开浏览器。勿用 3000/5173（3000 常被 Docker 占用）。

<details>
<summary>本地双进程开发（可选）</summary>

```bash
python dashboard/app.py          # 8765 API
cd dashboard/frontend && pnpm dev   # 5173 热更新
```

</details>

### 6. 工作室页 walkthrough（10 分钟）

| 步骤 | 操作 | 话术要点 |
|------|------|----------|
| 1 | 顶栏切换 **静海 → 灰域 → 暗夜 → 雪线 → 黄沙** | 多项目；**静海**为对外主打样章 |
| 2 | **质量仪表盘** | 覆盖率 / Golden Set 状态 |
| 3 | **Full-check 报告** | P0–P3 按章折叠（需已 generate report） |
| 4 | 生产控制台 Preflight 1–3 | 大纲门、canon 门 |
| 5 | 复制 Batch 命令 | 预算自动校准 + 15% 余量 |

Batch 后台运行需：`export LINGWEN_ALLOW_DASHBOARD_BATCH=1`

### 7. 可选 · 真实 pilot 1 章（10 分钟，耗 API）

```bash
export LINGWEN_ONBOARDING_PILOT=1
bash scripts/verify-onboarding.sh my-demo
```

或跟 [`studio-onboarding.md`](studio-onboarding.md) §3 跑 3 章。

### 8. Q&A 备忘

| 问题 | 回答 |
|------|------|
| 和「AI 写小说工具」差异？ | 硬门（大纲/pillars/max_chapter）+ 质检 + Golden Set 回归 |
| 星陨还写吗？ | testbed；默认 max_chapter=360 |
| 多久出一本短篇？ | 脚手架 5 分钟；10 章生产视 LLM 预算 |
| 如何保证质量？ | quick/full check + 人审 + Golden Set |

---

## Demo 检查清单

```bash
bash scripts/verify-studio-release.sh    # doctor + onboarding + golden-set ×8
```

- [x] `python lingwen.py doctor` 通过（默认星陨 root；Studio 书需 `unset LINGWEN_PROJECT_ROOT`）
- [x] `docs/trial-read-index.md` 八书链可开
- [x] `bash scripts/verify-onboarding-blind.sh` exit 0
- [x] `bash scripts/verify-golden-set.sh` ×**8**（七书 Studio + 星陨 testbed）
- [x] `python3 -m pytest tests/dashboard/test_studio_endpoints.py` 通过
- [x] （完整路线）Studio 页加载 + 多书切换 — **8765 单端口 + Cursor 内先点链接**
- [x] （完整路线）静海等 `full-check-report` 面板有数据

> 自动化记录：[`demo-checklist-report.md`](demo-checklist-report.md)

---

## 相关文档

- [`studio-demo-recording-script.md`](studio-demo-recording-script.md) — **30 分钟录屏分镜稿**
- [`studio-onboarding.md`](studio-onboarding.md) — 30 分钟第一本实操
- [`trial-read-index.md`](trial-read-index.md) — 对外分发
- [`onboarding-blind-report.md`](onboarding-blind-report.md) — 最新盲测记录
- [`HANDOFF.md`](../../HANDOFF.md) — 项目切换入口
