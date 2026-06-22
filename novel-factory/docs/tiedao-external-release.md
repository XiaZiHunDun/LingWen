# 《铁道档案》· 对外分发包

> **版本**：release-v1 · 2026-06-20  
> **状态**：**第三样章 · 可对外发送**  
> **体裁**：铁路悬疑 · 10 章短篇

---

## 发什么

| 对象 | 附件 | 路径 |
|------|------|------|
| **编辑 / 平台投稿** | 试读 **3 章**（推荐） | [`trial-read-ch001-003.md`](../projects/tiedao-dangan/docs/trial-read-ch001-003.md) |
| **内测 / 完整试读** | 全书 **10 章** | [`trial-read-ch001-010.md`](../projects/tiedao-dangan/docs/trial-read-ch001-010.md) |
| **产品侧（附带）** | 七样章索引 | [`trial-read-index.md`](trial-read-index.md) |

**一键打包目录**（推荐）：

```bash
bash scripts/prepare-tiedao-distribution.sh
# → projects/tiedao-dangan/dist/
```

| dist 内文件 | 用途 |
|-------------|------|
| `铁道档案-试读3章.md` | 投稿附件 |
| `铁道档案-全书10章.md` | 内测全书 |
| `投稿摘要.txt` | 平台简介框粘贴 |
| `邮件正文.txt` | 邮件正文复制 |
| `通读报告.md` | AI/编辑参考 |
| `质检报告.md` | P0/P1 机器报告 |
| `README.txt` | 发送说明 |

**七样章合集**：`bash scripts/prepare-studio-samples-zip.sh` → `dist/灵文工作室-七样章.zip`

---

## 三样章矩阵

| 书 | 对外角色 | 体裁 |
|----|----------|------|
| **静海日志** | 第一样章 · prose 定稿 | 沿海悬疑 |
| **灰域档案** | 第二样章 · 钩子最强 | 都市怪谈 |
| **铁道档案** | 第三样章 · 铁路档案 | 铁路悬疑 |

可单发一本，也可三册各附试读 3 章。

---

## 推荐试读章（编辑 5 分钟版）

| 时长 | 章节 | 理由 |
|------|------|------|
| 5 min | ch001 | 频道 5 · 道砟压痕 · 涵洞敲击 |
| +5 min | ch002 | **「那儿没涵洞啊」** 里程反转 |
| +5 min | ch003 | 竖井 · 路签 · 别跟桩走跟轨走 |

---

## 发前验收

```bash
cd novel-factory
bash scripts/prepare-tiedao-distribution.sh
bash scripts/verify-studio-release.sh
```

---

## 与 Studio 关系

《铁道档案》为灵文工作室 **11.03 第三本主修**，验证 prose rubric v1 + 校准脚本在铁路体裁上的可复制性。星陨 testbed 与本书无关。
