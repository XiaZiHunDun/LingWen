# 《静海日志》· 对外分发包

> **版本**：release-v2 · 2026-06-20  
> **状态**：**可立即对外发送** · Demo 录屏：**不做**  
> **体裁**：沿海悬疑 · 10 章短篇

---

## 发什么

| 对象 | 附件 | 路径 |
|------|------|------|
| **编辑 / 平台投稿** | 试读 **3 章**（推荐） | [`trial-read-ch001-003.md`](../projects/jinghai-rizhi/docs/trial-read-ch001-003.md) |
| **内测 / 完整试读** | 全书 **10 章** | [`trial-read-ch001-010.md`](../projects/jinghai-rizhi/docs/trial-read-ch001-010.md) |
| **产品侧（附带）** | 灵文工作室索引 | [`trial-read-index.md`](trial-read-index.md) |

复制到邮件 / 飞书 / 微信文件即可；Markdown 可原样发，或自行转 PDF/Word。

**一键打包目录**（推荐）：

```bash
bash scripts/prepare-jinghai-distribution.sh
# → projects/jinghai-rizhi/dist/
```

| dist 内文件 | 用途 |
|-------------|------|
| `静海日志-试读3章.md` | 投稿附件 |
| `投稿摘要.txt` | 平台简介框粘贴 |
| `邮件正文.txt` | 邮件正文复制 |
| `README.txt` | 发送说明 |

**七样章合集**（Studio 默认对外包）：

```bash
bash scripts/prepare-studio-samples-zip.sh
# → dist/灵文工作室-七样章.zip（含本册 dist/）
```

---

## 一句话

禁航日的静海港，沈舟在频道十七听见妹妹五年前的呼吸——盐渍指纹、十二条雾规、改档档案，把找人的故事写进港口的规则里。

---

## 简介（约 120 字 · 可直接粘贴）

《静海日志》是沿海悬疑短篇。禁航日，沈舟回到旧渡轮「海雾号」，在空白日志页上发现妹妹沈雁留下的盐渍指纹。对讲机频道十七传来无法解释的呼吸；灯塔里刻着「别上船」；老周念出十二条「雾规」——雾中不通讯，唯有「人未归时，第十七频道开放」。沈舟出海、下潜、改档、救援，在档案与海水之间，拼出妹妹自己选择的那条路。

---

## 简介（约 300 字 · 平台长简介）

静海港每年有十二天禁航日。沈舟每年都来海雾号旁守一次——五年前妹妹沈雁在这里失踪，卷宗写「推定死亡」，他却在对讲机频道十七里听见她的呼吸。

第一章从盐渍指纹和对讲机里的叹息起笔；第四章「雾规十二条」定下世界硬规则；后半改档、水密舱、录音笔与派出所收束，情感落在 ch009 救援。全文 10 章，约 2.3 万字（全书试读包），无 P0 叙事问题，可作为灵文工作室对外** prose 样章**。

**关键词**：沿海悬疑、档案、雾、兄妹、规则系怪谈（写实收束）

---

## 推荐试读章（编辑 5 分钟版）

若对方只看一章：发 **ch001**（入港调性）。  
若给 15 分钟：发 **ch001 + ch004**（雾规世界观）。  
若给情感验证：加 **ch009**（救援高潮）。

---

## 发前自检（已完成 2026-06-20）

```bash
bash scripts/prepare-jinghai-distribution.sh   # → projects/jinghai-rizhi/dist/
bash scripts/verify-studio-release.sh
```

- [x] 试读 3 章 / 10 章已重建  
- [x] `full-check-report.md` P0=0  
- [x] Golden Set 已同步  
- [x] 通读报告：[`jinghai-full-read-report.md`](jinghai-full-read-report.md)

---

## 邮件模板（可复制）

**主题**：《静海日志》试读样章（ coastal 悬疑 · 3 章）

正文：

> 附件为短篇小说《静海日志》试读前三章（禁航日 / 频道十七 / 雾规）。  
> 若需要全书 10 章或产品侧「灵文工作室」说明，请告知。  
> 谢谢阅读。

---

## 相关

- 对外分发：[`docs/jinghai-external-release.md`](docs/jinghai-external-release.md) · 打包：`bash scripts/prepare-jinghai-distribution.sh`
- Studio Demo 录屏：**本期不做**
