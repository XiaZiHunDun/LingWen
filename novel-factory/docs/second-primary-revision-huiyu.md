# 第二本主修 · 《灰域档案》（11.02）

> **启动**：2026-06-20 · Phase 11.02  
> **slug**：`huiyu-dangan`  
> **策略**：静海已定稿对外；灰域验证 **主修改稿流程可复用**（工程 + 通读改稿）

---

## 为什么选灰域（不是铁道）

| 维度 | 灰域 | 铁道 |
|------|------|------|
| 开篇钩子 | **ch001 异常信号/告示** 已立住 | 谜题巧，情感略薄 |
| 改稿目标 | 压 AI 味（句式单、agency） | 里程线精修 |
| 机器基线 | P0=0 · **P1=19** | P0=0 · P1 中等 |
| 与静海差异 | 都市悬疑 / 便利店视角 | 铁路档案模板 |

---

## 11.02 工程验收（已完成）

```bash
cd novel-factory
bash scripts/run-primary-revision-verify.sh huiyu-dangan   # PASS
bash scripts/prepare-huiyu-distribution.sh                 # → projects/huiyu-dangan/dist/
```

产出刷新：试读 3/10 章 · 投稿摘要 · 邮件正文 · 通读报告 · 质检报告

**dist 一键目录**：`projects/huiyu-dangan/dist/`（见 [`huiyu-external-release.md`](huiyu-external-release.md)）

---

## 通读指南（约 90 分钟）

1. 全书打包：[`trial-read-ch001-010.md`](../projects/huiyu-dangan/docs/trial-read-ch001-010.md)  
2. Dashboard：选 **灰域档案**  
3. 三栏笔记：**留 / 删 / 疑**（同静海流程）

### 建议阅读顺序

| 段 | 章 | 重点 |
|----|-----|------|
| **入局** | ch001–003 | 告示、编号、灰域规则 |
| **下潜** | ch004–006 | 供电局线、母亲档案 |
| **收束** | ch007–010 | 频道 / 身份 / 结局 |

### 机器优先扫（P1 密集）

| 章 | 提示 |
|----|------|
| ch001–004 | 句式多样性低 |
| ch003、006–008 | agency 偏低（林栀被动） |
| ch005 | 重复短语 |

---

## 改稿命令（定章后）

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/huiyu-dangan"
bash scripts/run-primary-revision-verify.sh huiyu-dangan
```

---

## 与静海关系

| 书 | 角色 |
|----|------|
| **静海日志** | 对外 prose 样章（定稿 v10.34） |
| **灰域档案** | 第二本主修 · 验证流程可复制 |
