# Studio Demo · 录屏就绪清单

> **版本**：record-ready-v1 · 2026-06-20  
> **对应分镜**：[`studio-demo-recording-script.md`](studio-demo-recording-script.md) recording-v3  
> **状态**：自动化项 ✅ · **本期不录屏**（备查）

---

## 录屏前 2 分钟（复制粘贴）

```bash
cd novel-factory
bash scripts/verify-studio-release.sh    # 应 ending: Studio release verify passed

bash scripts/run-dashboard-single-port.sh   # 8765 单端口，另开终端
```

浏览器（Cursor SSH）：

1. Ports 确认 **8765** 转发  
2. **先在 IDE 内点击** `http://127.0.0.1:8765/?nav=studio`  
3. 再开浏览器同地址  

---

## 预开标签

| Tab | 内容 |
|-----|------|
| A | `http://127.0.0.1:8765/?nav=studio` |
| B | `docs/trial-read-index.md` |
| C | `projects/jinghai-rizhi/docs/trial-read-ch001-003.md`（**主打样章**） |
| D | `HANDOFF.md` §0 TL;DR |

---

## 自动化验收（2026-06-20）

| 项 | 结果 |
|----|------|
| `verify-studio-release.sh` | ✅ PASS |
| 静海 `trial-read-ch001-003/010` | ✅ 已重建 |
| 静海 `full-check-report.md` | ✅ P0=0 |
| 静海 Golden Set | ✅ ch001/005/010 |
| 对外分发包 | ✅ [`jinghai-external-release.md`](jinghai-external-release.md) |

---

## 录屏时展示顺序（简版）

1. HANDOFF TL;DR → 星陨 testbed / 工作室产品  
2. **静海** trial-read ch001（频道十七）  
3. 终端：`verify-studio-release.sh`（可剪 5 秒 PASS 片段）  
4. Dashboard：ProjectSwitcher → **静海日志** → Full-check 面板  
5. 终端：`verify-golden-set.sh jinghai-rizhi`  
6. 收尾：trial-read-index + 「新书 = init-project 同样流程」

---

## 标准收尾词

1. 和通用 AI 写作工具的差别：**硬门 + 质检 + Golden Set**，不是无限续写。  
2. 成功看闭环：**10 章 + 试读包 + P0=0**，不看章数 KPI。  
3. 对外样章：**《静海日志》** 已定稿；新书改 pillars/大纲走同一 pipeline。

---

## 人工项（开录前 30 秒）

- [ ] 麦克风试录  
- [ ] 关系统通知  
- [ ] 终端字号 ≥ 14pt，浏览器 125%  
- [ ] Dashboard 顶栏能看到多项目  

**无法代劳**：实际录屏需你本地操作；本清单保证素材与 smoke 已绿。
