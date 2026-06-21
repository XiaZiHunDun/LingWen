# 《暗河档案》· 对外分发包

> **版本**：release-v1 · 2026-06-20  
> **状态**：**第七样章 · 可对外发送**  
> **体裁**：喀斯特悬疑 · 10 章短篇

---

## 发什么

| 对象 | 附件 | 路径 |
|------|------|------|
| **编辑 / 平台** | 试读 **3 章** | [`trial-read-ch001-003.md`](../projects/anhe-dangan/docs/trial-read-ch001-003.md) |
| **内测** | 全书 **10 章** | [`trial-read-ch001-010.md`](../projects/anhe-dangan/docs/trial-read-ch001-010.md) |

**一键打包**：

```bash
bash scripts/prepare-anhe-distribution.sh
# → projects/anhe-dangan/dist/
```

---

## 推荐试读章

| 章 | 理由 |
|----|------|
| ch001 | 第三频道呼吸波形 / 空白本 |
| ch002 | 暗河改道 / 声呐图对不上 |
| ch003 | 竖井 / 金属敲击回应 |

---

## 发前自检

```bash
bash scripts/run-prose-calibration.sh anhe-dangan
bash scripts/prepare-anhe-distribution.sh
```

- [x] Golden Set P0=0  
- [x] prose 校准 PASS（prose_p1≤12）  
- [x] LLM Golden：`llm-golden-primary` job（七样章 blocking · 需 `MINIMAX_API_KEY`）

相关：[`seventh-primary-revision-anhe.md`](seventh-primary-revision-anhe.md)
