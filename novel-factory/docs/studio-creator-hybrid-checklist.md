# Studio 创作者 Hybrid 走通 Checklist

> Studio 工厂 KPI 项目也可使用创作页做卷纲/设定管理；守门仍为全量 Studio 门。  
> 冒烟：`bash scripts/verify-studio-creator-hybrid.sh`（无 LLM）

## 适用场景

- 已有 `creation_mode: studio` 的样章/新书
- 想用 **创作页三栏** 管卷纲与设定，但 **验收仍走 Studio**（judge / prose / golden）

## 1. 确认模式

```bash
export LINGWEN_PROJECT_ROOT="$(pwd)/projects/your-studio-book"
grep creation_mode config/project.yaml
# 应为 studio + quality_profile: studio_full（或默认）
```

## 2. 创作页（`?nav=write`）

- [ ] **脉络**：侧滑抽屉或 Tab → 套用卷纲模板（三幕/五卷）→ 锁定 → 保存
- [ ] **设定**：Tab 打开 → 编辑 → 三路 diff（磁盘 / 编辑器 / 历史）→ 确认保存
- [ ] **写**：human-first 书桌；顶栏 **导出 / 发布**；工厂正文仍以 batch 产出为主

## 3. Studio 生产

```bash
export LINGWEN_PRODUCTION_MODE=canon
python -m infra.agent_system.chapter_production_batch \
  --preflight-only --start-chapter 1 --max-chapters 3 --dry-run
```

真跑 batch 见 [`studio-onboarding.md`](studio-onboarding.md)。

## 4. Studio 验收（非 companion P0-only）

```bash
python lingwen.py check --full
# 或项目级 studio 验收脚本
```

## 通过标准

| 项 | 标准 |
|----|------|
| 创作页 | studio 项目可打开 creator 三栏 |
| 卷纲模板 | `apply-template` 生成合理章范围 |
| 预检 | batch preflight dry-run OK |
| 模式 | `creation_mode=studio` 不变 |

## 相关

- [`creator-onboarding.md`](creator-onboarding.md)
- [`companion-walkthrough-checklist.md`](companion-walkthrough-checklist.md)
