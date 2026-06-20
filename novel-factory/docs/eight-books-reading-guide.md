# 灵文工作室 · 七书通读指南

> **版本**：reading-v2 · 2026-06-20  
> **阶段**：静海样章定稿 · 七书封存 · 按需改稿  
> **入口**：[`trial-read-index.md`](trial-read-index.md)

---

## 怎么读

1. **先试读 3 章**：每书 `projects/<slug>/docs/trial-read-ch001-003.md`，约 15–20 分钟/本。
2. **喜欢的再读全书**：`trial-read-ch001-010.md`。
3. **要改哪章**：直接说「改 `<slug>` ch00X」→ 改文 → `generate-full-check-report.sh` → 必要时更新 Golden Set。

Dashboard 本地：`bash scripts/run-dashboard-single-port.sh`，浏览器打开 `http://127.0.0.1:8765/?nav=studio`（Cursor 内先点链接，Ports 转发 **8765**）。

---

## 主修书（样章定稿）

**《静海日志》** · `jinghai-rizhi` · **对外主打** · 详见 [`primary-revision-book.md`](primary-revision-book.md)

| 包 | 链接 |
|----|------|
| 试读 3 章 | [`trial-read-ch001-003.md`](../projects/jinghai-rizhi/docs/trial-read-ch001-003.md) |
| 全书 10 章 | [`trial-read-ch001-010.md`](../projects/jinghai-rizhi/docs/trial-read-ch001-010.md) |
| 通读报告 | [`jinghai-full-read-report.md`](jinghai-full-read-report.md) |

---

## 七书一览

| # | 书名 | slug | 体裁 | 主角 | 核心钩子 | P0 | P1 | 试读 3 章 |
|---|------|------|------|------|----------|----|----|-----------|
| 1 | 《灰域档案》 | huiyu-dangan | 都市怪谈 | 林栀 | 「你看到了。」 | 0 | 20 | [试读](projects/huiyu-dangan/docs/trial-read-ch001-003.md) |
| 2 | 《暗夜信标》 | anye-xinbiao | 科幻悬疑 | — | 信标脉冲 | 0 | 12 | [试读](projects/anye-xinbiao/docs/trial-read-ch001-003.md) |
| 3 | 《静海日志》 | jinghai-rizhi | 沿海悬疑 | — | 雾港·频道十七 | 0 | 10 | [试读](projects/jinghai-rizhi/docs/trial-read-ch001-003.md) |
| 4 | 《雪线档案》 | xuexian-dangan | 高山悬疑 | 方朔 | 封山·频道 9 | 0 | 10 | [试读](projects/xuexian-dangan/docs/trial-read-ch001-003.md) |
| 5 | 《黄沙档案》 | huangsha-dangan | 沙漠悬疑 | 陆沉/顾遥 | 沙丘带·录音机 | 0 | 14 | [试读](projects/huangsha-dangan/docs/trial-read-ch001-003.md) |
| 6 | 《暗河档案》 | anhe-dangan | 喀斯特悬疑 | 沈渡/林湄 | 丰水期·频道 3 | 0 | 14 | [试读](projects/anhe-dangan/docs/trial-read-ch001-003.md) |
| 7 | 《铁道档案》 | tiedao-dangan | 铁路悬疑 | 纪川/方晓 | K47·频道 5 | 0 | 15 | [试读](projects/tiedao-dangan/docs/trial-read-ch001-003.md) |

**全书打包**：各书 `projects/<slug>/docs/trial-read-ch001-010.md`  
**质检报告**：各书 `projects/<slug>/docs/full-check-report.md`

---

## 建议阅读顺序

**按体裁递进**（怪谈 → 科幻 → 地理档案线）：

1. 灰域档案 → 暗夜信标  
2. 静海日志 → 雪线档案  
3. 黄沙档案 → 暗河档案 → 铁道档案（后三本 ch004–010 为写实模板改写，风格接近）

**按改稿优先级**（P1 多、LLM 初稿感强）：

1. **灰域档案** — ch001–010 句式单一、「她感到」重复多  
2. **铁道 / 暗河 / 黄沙** — ch001–003 LLM 初稿；ch005+ 已写实化  
3. **静海 / 雪线 / 暗夜** — P1 相对较少，通读体验可能更顺

---

## 改稿备忘（机器检出 · 非必须全改）

| 类型 | 说明 | 典型位置 |
|------|------|----------|
| `sentence_diversity_low` | 单一句式占比 >40% | 各书 ch001–010 普遍存在 |
| `repetitive_phrase` | 「他/她感到」过密 | 灰域、铁道、暗河、黄沙 ch001–008 |
| `low_character_agency` | 主角被动反应多 | 各书零散章节 |
| `causal_chain_break` | 因果/时间线矛盾 | 黄沙 ch004（已修：录音时长 vs 未返回） |

P1 多为文风/ agency 类，**不影响 P0 硬门**；个人通读时凭语感决定是否改。

---

## 改稿命令（单章定稿后）

```bash
cd novel-factory
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/<slug>"

bash scripts/generate-full-check-report.sh <slug> 1 10
bash scripts/build-trial-read.sh <slug> 1 10
bash scripts/sync-golden-set.sh <slug>    # 改文后同步 Golden 快照
bash scripts/verify-golden-set.sh <slug>
```

---

## 试验田（非 Studio 短篇）

| 书 | 说明 | 试读 |
|----|------|------|
| 《星陨纪元》 | testbed · 正史 ch001–360 | [`docs/trial-read-ch001-003.md`](docs/trial-read-ch001-003.md) |

---

## 本期不做

- 开第九本 Studio 短篇（除非你明确要求）  
- Demo 录屏  
- 用 3000/5173 作 Dashboard 入口
