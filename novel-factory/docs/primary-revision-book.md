# 主修书 · 样章矩阵

> **更新**：2026-06-20 · Phase 11.22 顶级工作室路线  
> **标准**：[`prose-rubric-v1.md`](prose-rubric-v1.md) · [`top-tier-studio-gap-v1.md`](top-tier-studio-gap-v1.md)

| 书 | slug | 角色 | 状态 | dist |
|----|------|------|------|------|
| **静海日志** | `jinghai-rizhi` | 第一样章 · 沿海悬疑 | ✅ 定稿 | ✅ |
| **灰域档案** | `huiyu-dangan` | 第二样章 · 都市怪谈 | ✅ 三轮改稿 | ✅ |
| **铁道档案** | `tiedao-dangan` | 第三样章 · 铁路档案 | ✅ 11.03 dist | ✅ |
| **暗夜信标** | `anye-xinbiao` | 第四样章 · 科幻悬疑 | ✅ dist | ✅ |
| **雪线档案** | `xuexian-dangan` | 第五样章 · 高山悬疑 | ✅ dist | ✅ |
| 其余三书 | — | 封存 P0=0 | — | — |

---

## 验收命令（任意主修书）

```bash
cd novel-factory
bash scripts/run-primary-revision-verify.sh <slug>   # P0 + prose + LLM Golden blocking（五样章）
bash scripts/run-prose-calibration.sh <slug>
bash scripts/run-llm-golden-primary.sh               # 五书 LLM 一次跑齐
```

---

## 《静海日志》· 第一样章

**对外主打** · prose 标杆 · 详见 [`jinghai-full-read-report.md`](jinghai-full-read-report.md)

| 包 | 链接 |
|----|------|
| 试读 3 章 | [`trial-read-ch001-003.md`](../projects/jinghai-rizhi/docs/trial-read-ch001-003.md) |
| dist | `projects/jinghai-rizhi/dist/` |

---

## 《灰域档案》· 第二样章

详见 [`second-primary-revision-huiyu.md`](second-primary-revision-huiyu.md) · [`huiyu-full-read-report.md`](huiyu-full-read-report.md)

| 包 | 链接 |
|----|------|
| dist | `projects/huiyu-dangan/dist/` |

---

## 《铁道档案》· 第三样章（当前主修）

详见 [`third-primary-revision-tiedao.md`](third-primary-revision-tiedao.md)

**为什么选铁道**：试读 TOP3、谜题完成度高、与静海/灰域体裁差异大，适合验证 rubric 在第三本的 ROI。

---

## 改稿备忘（七书）

[`eight-books-reading-guide.md`](eight-books-reading-guide.md) · [`seven-books-trial-read-report.md`](seven-books-trial-read-report.md)
