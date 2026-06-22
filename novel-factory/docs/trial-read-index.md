# 灵文工作室 · 试读分发索引

> **版本**：distribution-v8 · 2026-06-22 · **七样章 dist + zip（默认）**  
> **用途**：对外分发时，直接发送下方「单文件试读」链接或附件。

---

## 七样章（对外默认）

打包：`bash scripts/prepare-studio-samples-zip.sh` → `dist/灵文工作室-七样章.zip`

| 书 | 角色 | 试读 3 章 | 全书 10 章 | 打包 |
|----|------|-----------|------------|------|
| **《静海日志》** | 第一样章 · 沿海 | [`trial-read-ch001-003.md`](projects/jinghai-rizhi/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/jinghai-rizhi/docs/trial-read-ch001-010.md) | `prepare-jinghai-distribution.sh` |
| **《灰域档案》** | 第二样章 · 怪谈 | [`trial-read-ch001-003.md`](projects/huiyu-dangan/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/huiyu-dangan/docs/trial-read-ch001-010.md) | `prepare-huiyu-distribution.sh` |
| **《铁道档案》** | 第三样章 · 铁路 | [`trial-read-ch001-003.md`](projects/tiedao-dangan/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/tiedao-dangan/docs/trial-read-ch001-010.md) | `prepare-tiedao-distribution.sh` |
| **《暗夜信标》** | 第四样章 · 科幻 | [`trial-read-ch001-003.md`](projects/anye-xinbiao/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/anye-xinbiao/docs/trial-read-ch001-010.md) | `prepare-anye-distribution.sh` |
| **《雪线档案》** | 第五样章 · 高山 | [`trial-read-ch001-003.md`](projects/xuexian-dangan/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/xuexian-dangan/docs/trial-read-ch001-010.md) | `prepare-xuexian-distribution.sh` |
| **《黄沙档案》** | 第六样章 · 沙漠 | [`trial-read-ch001-003.md`](projects/huangsha-dangan/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/huangsha-dangan/docs/trial-read-ch001-010.md) | `prepare-huangsha-distribution.sh` |
| **《暗河档案》** | 第七样章 · 喀斯特 | [`trial-read-ch001-003.md`](projects/anhe-dangan/docs/trial-read-ch001-003.md) | [`trial-read-ch001-010.md`](projects/anhe-dangan/docs/trial-read-ch001-010.md) | `prepare-anhe-distribution.sh` |

**精简五册 zip**（可选）：`STUDIO_SAMPLES=5 bash scripts/prepare-studio-samples-zip.sh` → [`dist/灵文工作室-五样章.zip`](../dist/灵文工作室-五样章.zip)

说明：[`jinghai-external-release.md`](jinghai-external-release.md) · … · [`anhe-external-release.md`](anhe-external-release.md)

---

## 历史：五样章优先（v10）

以下为 v10 对外叙事；**v12 默认七册**，上表为准。

<details>
<summary>展开五样章表（归档）</summary>

| 书 | 角色 |
|----|------|
| 静海 · 灰域 · 铁道 · 暗夜 · 雪线 | 前五样章 |

</details>

---

## ~~扩展样章~~（已并入上表）

~~第六 / 七~~ 已合并至 **七样章（对外默认）**。

---

## 八书工程

- [`docs/eight-books-reading-guide.md`](eight-books-reading-guide.md) — 通读顺序 · 改稿备忘  
- `bash scripts/verify-studio-release.sh` — golden-set ×8 · doctor · onboarding

---

## 试验田（星陨纪元 · 开篇抽样）

| 书 | 试读 | 说明 |
|----|------|------|
| 《星陨纪元》 | [`docs/trial-read-ch001-003.md`](docs/trial-read-ch001-003.md) | testbed 开篇 3 章；正史 ch001–360 |

索引：[`docs/trial-read-xingyun.md`](docs/trial-read-xingyun.md)

> 全书正文体量大（360 章），对外分发建议仅用试读 3 章或既有发布归档 `08_已发布/`。

---

## 一键重建

```bash
cd novel-factory
bash scripts/build-all-trial-reads.sh
```

单项目：

```bash
bash scripts/build-trial-read.sh huiyu-dangan 1 3
bash scripts/build-trial-read.sh anye-xinbiao 1 10
bash scripts/build-trial-read.sh jinghai-rizhi 1 3
bash scripts/build-trial-read.sh xingyun-jiyuan 1 3
```

---

## 分发建议

1. **编辑 / 平台投稿**：五样章任选，或发 **五册 zip**
2. **内测读者**：发 `trial-read-ch001-010.md`（全书 10 章）
3. **产品演示**：附 [`studio-demo.md`](studio-demo.md) · 分发说明见 jinghai/huiyu-external-release
4. **工程验收**：`bash scripts/verify-studio-release.sh`
