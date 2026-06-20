# 第三本主修 · 《铁道档案》（11.03）

> **启动**：2026-06-20 · Phase 11.03  
> **slug**：`tiedao-dangan`  
> **策略**：静海 + 灰域 dist 已闭环；铁道验证 **prose rubric v1** 在第三本书上的 ROI

---

## 为什么选铁道（不是暗夜）

| 维度 | 铁道 | 暗夜 |
|------|------|------|
| 试读排名 | **七书 TOP3**（谜题 + prose） | TOP3（类型感最完整） |
| 与灰域差异 | 铁路档案 / K47·频道 5 | 科幻射电，改稿方向不同 |
| 情感线 | 纪川 / 方晓 — 有张力 | 顾岚线好，但科幻俗套需额外处理 |
| 机器基线 | P0=0 · P1≈15 | P0=0 · P1≈12 |
| dist 价值 | **档案线第三本**，补全地理系列 | 可作为第四本 |

七书试读结论：铁道 **谜题巧、类型完成度高**，改稿重点是 **里程线精修 + 减模板 fatigue**，而非灰域式大规模压 AI 味。

---

## 11.03 目标

| 项 | 目标 |
|----|------|
| Prose rubric | 加权均分 ≥ 4.0 |
| P0 | 0 |
| prose 类 P1 | ≤ 14（见 `config/prose_calibration.yaml`） |
| dist | `prepare-tiedao-distribution.sh` → `projects/tiedao-dangan/dist/` |
| 通读报告 | `docs/tiedao-full-read-report.md` |

---

## 11.03 工程验收（✅ 已完成）

```bash
cd novel-factory
bash scripts/run-primary-revision-verify.sh tiedao-dangan   # PASS · prose_p1=8
bash scripts/prepare-tiedao-distribution.sh                 # → projects/tiedao-dangan/dist/
```

**dist**：`projects/tiedao-dangan/dist/` · 见 [`tiedao-external-release.md`](tiedao-external-release.md)

---

## 通读指南（约 90 分钟）

1. 全书：[`trial-read-ch001-010.md`](../projects/tiedao-dangan/docs/trial-read-ch001-010.md)  
2. Dashboard：选 **铁道档案** → 查看 **Prose 热力图**  
3. 三栏笔记：**留 / 删 / 疑**

### 建议阅读顺序

| 段 | 章 | 重点 |
|----|-----|------|
| **月台** | ch001–003 | K47、频道 5、纪川/方晓立住 |
| **区间** | ch004–006 | 档案线、里程异常 |
| **终到** | ch007–010 | 身份、收束、钩子回收 |

### 机器优先扫

| 章 | 提示 |
|----|------|
| ch001–003 | LLM 初稿感 · 句式多样性 |
| ch004–006 | 与黄沙/暗河结构相近 — 防模板疲劳 |
| ch007–010 | agency · 章末钩子 |

---

## 与样章矩阵

| 书 | 角色 | dist |
|----|------|------|
| 静海日志 | 第一样章 · 沿海悬疑 | ✅ |
| 灰域档案 | 第二样章 · 都市怪谈 | ✅ |
| **铁道档案** | **第三样章 · 铁路档案** | 📋 11.03 | ✅ |

---

## 改稿后

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/tiedao-dangan"
bash scripts/run-primary-revision-verify.sh tiedao-dangan
bash scripts/run-prose-calibration.sh tiedao-dangan
```

详见 [`prose-rubric-v1.md`](prose-rubric-v1.md) · [`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md)
