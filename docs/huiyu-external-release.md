# 《灰域档案》· 对外分发包

> **版本**：release-v1 · 2026-06-20  
> **状态**：**第二样章 · 可对外发送**  
> **体裁**：都市怪谈 · 10 章短篇

---

## 发什么

| 对象 | 附件 | 路径 |
|------|------|------|
| **编辑 / 平台投稿** | 试读 **3 章**（推荐） | [`trial-read-ch001-003.md`](../projects/huiyu-dangan/docs/trial-read-ch001-003.md) |
| **内测 / 完整试读** | 全书 **10 章** | [`trial-read-ch001-010.md`](../projects/huiyu-dangan/docs/trial-read-ch001-010.md) |
| **产品侧（附带）** | 七样章索引 | [`trial-read-index.md`](trial-read-index.md) |

**一键打包目录**（推荐）：

```bash
bash scripts/prepare-huiyu-distribution.sh
# → projects/huiyu-dangan/dist/
```

| dist 内文件 | 用途 |
|-------------|------|
| `灰域档案-试读3章.md` | 投稿附件 |
| `灰域档案-全书10章.md` | 内测全书 |
| `投稿摘要.txt` | 平台简介框粘贴 |
| `邮件正文.txt` | 邮件正文复制 |
| `通读报告.md` | AI/编辑参考 |
| `质检报告.md` | P0/P1 机器报告 |
| `README.txt` | 发送说明 |

**七样章合集**：`bash scripts/prepare-studio-samples-zip.sh` → `dist/灵文工作室-七样章.zip`

---

## 与《静海日志》的分工

| 书 | 对外角色 | 体裁 |
|----|----------|------|
| **静海日志** | 第一样章 ·  prose 定稿 | 沿海悬疑 |
| **灰域档案** | 第二样章 · 钩子最强 | 都市怪谈 / 档案恐怖 |

对外可以只发一本，也可以 **静海 + 灰域** 各附 3 章，证明工作室跨体裁可复制。

---

## 推荐试读章（编辑 5 分钟版）

| 时长 | 章节 | 理由 |
|------|------|------|
| 5 分钟 | ch001 | 裂纹 / 干燥纸角 / 「你看到了」 |
| +10 分钟 | ch003 | 灰域 #0421 推送 + 周姐便签 |
| 情感验证 | ch010 | 底片 / 「上车的人」/ 身份收束 |

---

## 发前自检

```bash
bash scripts/prepare-huiyu-distribution.sh
bash scripts/verify-studio-release.sh
```

- [x] 三轮 prose 改稿 + `run-primary-revision-verify.sh` PASS  
- [x] `full-check-report.md` P0=0  
- [x] Golden Set 已同步  
- [x] 通读报告：[`huiyu-full-read-report.md`](huiyu-full-read-report.md)

---

## 相关文档

- 主修流程：[`second-primary-revision-huiyu.md`](second-primary-revision-huiyu.md)  
- 静海分发（第一样章）：[`jinghai-external-release.md`](jinghai-external-release.md)
