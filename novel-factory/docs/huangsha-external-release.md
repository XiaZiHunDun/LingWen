# 《黄沙档案》· 对外分发包

> **版本**：release-v1 · 2026-06-20  
> **状态**：**第六样章 · 可对外发送**  
> **体裁**：沙漠悬疑 · 10 章短篇

---

## 发什么

| 对象 | 附件 | 路径 |
|------|------|------|
| **编辑 / 平台** | 试读 **3 章** | [`trial-read-ch001-003.md`](../projects/huangsha-dangan/docs/trial-read-ch001-003.md) |
| **内测** | 全书 **10 章** | [`trial-read-ch001-010.md`](../projects/huangsha-dangan/docs/trial-read-ch001-010.md) |

**一键打包**：

```bash
bash scripts/prepare-huangsha-distribution.sh
# → projects/huangsha-dangan/dist/
```

---

## 推荐试读章

| 章 | 理由 |
|----|------|
| ch001 | 风蚀预警 / 空白观测本 / 顾遥痕迹 |
| ch003 | 「出事以后第三天」录音线 |
| ch004 | 因果修：录音时长 vs 未返回（已修） |

---

## 发前自检

```bash
bash scripts/run-prose-calibration.sh huangsha-dangan   # prose_p1≤12 · P0=0
bash scripts/prepare-huangsha-distribution.sh
```

- [x] Golden Set P0=0  
- [x] prose 校准 PASS（prose_p1=8）  
- [ ] 可选：有 key 时 `bash scripts/run-llm-golden-check.sh huangsha-dangan`

相关：[`sixth-primary-revision-huangsha.md`](sixth-primary-revision-huangsha.md)
