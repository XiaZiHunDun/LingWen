# 灵文工作室 (LingWen Studio) V3.1 架构优化方案

> **版本**: V3.1 | **日期**: 2026-07-30
> **参考来源**: 78 个 Agent 项目深度技术选型分析 + AI 开发防错设计大全
> **变更说明**: 基于 V3.0 的自我评审修订 — 砍掉过度工程、重组优先级、映射到 L0-L7、增加迁移策略和"明确不做"清单
> **核心定位**: 在 V2.0 八层架构基础上做增量优化，不做推倒重来

---

## 目录

1. [V3.0→V3.1 修订说明](#v30v31-修订说明)
2. [领域分析：小说创作的独特挑战](#1-领域分析小说创作的独特挑战)
3. [现有基础盘点](#2-现有基础盘点)
4. [优化方向总览](#3-优化方向总览)
5. [A. 开发防错体系（横切 L0-L7）](#a-开发防错体系横切-l0-l7)
6. [B. L2 创作引擎优化](#b-l2-创作引擎优化)
7. [C. L3 一致性免疫增强](#c-l3-一致性免疫增强)
8. [D. L5 AI 编排与上下文工程](#d-l5-ai-编排与上下文工程)
9. [E. L5/L6 记忆系统增强](#e-l5l6-记忆系统增强)
10. [F. L1 前端架构优化](#f-l1-前端架构优化)
11. [G. 类型驱动工程实践（横切）](#g-类型驱动工程实践横切)
12. [H. 发布与质量体系](#h-发布与质量体系)
13. [明确不做清单](#明确不做清单)
14. [实施路线图（含迁移策略）](#实施路线图含迁移策略)
15. [关键指标目标](#关键指标目标)

---

## V3.0→V3.1 修订说明

### 砍掉的内容（过度工程）

| 砍掉项 | 原因 | 替代方案 |
|--------|------|----------|
| MCP 协议标准化 | 灵文是独立应用，内部工具不需要跨工具互操作 | 保留声明式工具注册，不引入 MCP 协议外壳 |
| 六阶段权限评估流水线 | 为代码执行沙箱设计，创作场景不需要 | 保留简单的权限分级（read/write/dangerous） |
| 三平台沙箱隔离 | 代码执行场景，不适用于创作 | 保留用户输入隔离即可 |
| 默认多 Agent Squad | 每次创作 4 Agent + 3 辩论 + 1 审查 = 8x AI 调用，成本爆炸 | 保留单 Agent 为默认，多 Agent 为可选高级模式 |
| 三方辩论模式 | 每个争议 3x LLM + 判官 = 4x 调用，与"成本即边界"矛盾 | 保留简单的写审分离（2x 调用） |
| 向量库长期记忆 | 小说世界观是结构化数据，SQLite 更适合 | 用现有 world_model/ + persistence/ 增强 |

### 重新排列的优先级

| V3.0 优先级 | V3.1 优先级 | 调整原因 |
|-------------|-------------|----------|
| P0: AI 防错体系 | P1: 开发防错 | 这是开发流程优化，不是产品功能，紧急度低于用户体验 |
| P0: Agent 编排 | P2: 可选高级模式 | 单 Agent 已可用，多 Agent 是锦上添花 |
| P1: 上下文工程 | P0: 上下文缓存 | 直接降低 AI 成本和响应时间，用户可感知 |
| P1: 工具系统 MCP | 删除 | 不需要 |
| P1: 记忆系统 | P1: 记忆增强 | 基于现有 world_model/ 增强，非重构 |
| P2: 安全治理 | 精简后 P2 | 只保留用户输入隔离和 Prompt 注入防御 |
| P2: 前端架构 | P0: Composable 拆分 | 直接影响代码可维护性 |
| P1: 类型驱动 | P1: 类型强化 | 保持不变 |
| P2: Skill 契约 | P1: 创作 Skill | 提升到 P1，直接提升 AI 创作质量 |

---

## 1. 领域分析：小说创作的独特挑战

### 1.1 与其他 AI 应用的本质区别

| 维度 | 代码/Agent 项目 | 灵文（小说创作） |
|------|----------------|-----------------|
| **输出性质** | 确定性（代码要么对要么错） | 主观性（好文笔没有标准答案） |
| **质量度量** | 测试通过率、覆盖率 | 读者体验、一致性、创意新颖度 |
| **AI 角色** | 工具（辅助编码） | 协作者（共同创作） |
| **上下文规模** | 代码库（可索引） | 100+ 章节叙事（不可索引） |
| **修改影响** | 编译错误（可检测） | 静默断裂（难以检测） |
| **核心风险** | Bug、安全漏洞 | 人物 OOC、伏笔断裂、世界观漂移 |

### 1.2 创作领域四大独特挑战

| 挑战 | 描述 | 当前处理方式 | 优化方向 |
|------|------|-------------|----------|
| **创意保护** | 防止 AI 同质化创作（所有章节风格趋同） | 无系统化机制 | AI Tells 黑名单 + 风格多样性检查 |
| **节奏管理** | 100+ 章节长篇的叙事节奏控制 | PacingChecker | 节奏热力图 + 卷级节奏规划 |
| **读者体验** | 最终质量指标是读者体验，不是代码质量 | ReadingPowerEngine | 阅读力分析 + 体验评分 |
| **自由度 vs 一致性** | 过度检查会扼杀创意 | 仲裁器分级（钻石/黄金/白银/青铜） | 保持分级，增加"创意豁免"白名单 |

### 1.3 用户画像约束

> 用户偏好: 界面简洁（按钮 ≤ 15）、不喜欢复杂技术细节、偏好直观操作

**架构原则**: 复杂度封装在后端，UI 只暴露最简操作。用户不需要知道"哪个 Agent 在工作"，只需要看到"章节正在生成"。

---

## 2. 现有基础盘点

### 2.1 已有的核心资产（不推倒重来）

| 层级 | 已有资产 | 规模 | 质量 |
|------|----------|------|------|
| **L0 故事契约** | 契约引擎、路由器、反模式检测、注入器 | 6 文件 | 已实现 |
| **L2 创作引擎** | MasterController、章节生产管线（5 种）、MC 写作/编辑/工作流 | 12+ 文件 | 已实现 |
| **L3 一致性免疫** | 20+ 规则检查器、7 LLM 增强检查器、9 修复器、仲裁器 | 40+ 文件 | 核心已实现 |
| **L4 跨卷涟漪** | 涟漪引擎、级联系统、引用图、审计留存、LLM 扫描、缓存 | 16 文件 | 已实现 |
| **L5 AI 编排** | 多 Provider 抽象、TieredRouter、成本追踪、Prompt 工程、GOT | 20+ 文件 | 已实现 |
| **L5 世界模型** | WorldModelEngine、注册表、快照、关键点图、生命周期 | 8 文件 | 已实现 |
| **L6 持久化** | SQLite + 原生 SQL、EventSourcing、状态管理、导出、钩子 | 15+ 文件 | 已实现 |
| **L7 洞察进化** | 阅读力引擎、质量协调、生产记录、剧情子图 | 15+ 文件 | 已实现 |
| **前端** | 13 页面、40+ Composables、4 Pinia Store、150 测试文件 | 918 测试 | 全部通过 |

### 2.2 已完成的技术债清理

| 项目 | 状态 |
|------|------|
| 前端 TS 迁移（核心 Composable 已转 .ts） | ✅ 已完成 |
| 后端异常细化（28 处 Exception → 具体类型） | ✅ 已完成 |
| 前端静默错误处理消除（16 处 catch null） | ✅ 已完成 |
| 废弃代码清理（4 处 @deprecated） | ✅ 已完成 |
| Composable JSDoc 补全（8 核心文件） | ✅ 已完成 |
| defineProps JSDoc 补全（63 组件） | ✅ 已完成 |
| Pinia Store JSDoc 补全 | ✅ 已完成 |
| API 层 JSDoc 补全 | ✅ 已完成 |
| eslint.config.js 扩展（no-store-value-access 等） | ✅ 已完成 |

### 2.3 当前技术债务（需优化）

| 债务 | 严重度 | 影响 |
|------|--------|------|
| ~30 Composable 仍是 .js | 中 | 类型安全不完整 |
| useCreatorWriteWorkbench 49 字段 | 高 | 单一 Composable 过重 |
| 上下文构建无缓存 | 中 | AI 调用成本高（每次重建完整上下文） |
| 检查器误报率未知 | 中 | 可能影响创作体验 |
| 无 AGENTS.md 架构契约 | 中 | AI 协作者可能破坏架构不变量 |
| 前端部分 .js 文件无类型保护 | 低 | 边际风险 |
| infra/ 根目录 30+ flat .py 文件 | 低 | 模块化不足 |

---

## 3. 优化方向总览

### 3.1 八层映射

```
┌──────────────────────────────────────────────────────────────┐
│  L0 故事契约  ←  A 开发防错（AGENTS.md 架构不变量）          │
│  L1 接入呈现  ←  F 前端架构优化（Composable 拆分）           │
│  L2 创作引擎  ←  B 创作引擎优化（单 Agent 增强 + 可选多 Agent）│
│  L3 一致性免疫 ←  C 一致性增强（误报率优化 + 创意豁免）       │
│  L4 跨卷涟漪   ←  （已成熟，维持）                            │
│  L5 AI 编排   ←  D 上下文工程（缓存 + 增量 + 压缩）           │
│  L5/L6 记忆   ←  E 记忆增强（基于 world_model/ 增量）        │
│  L6 持久化    ←  （已成熟，维持）                              │
│  L7 洞察进化  ←  （已成熟，维持）                              │
│  横切关注点   ←  A 开发防错 + G 类型驱动 + H 质量体系         │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 优化方向优先级

| 代号 | 方向 | 影响层级 | 优先级 | 工作量 | 用户可感知 |
|------|------|----------|--------|--------|-----------|
| **F** | 前端架构优化（Composable 拆分） | L1 | P0 | 中 | ✅ 性能提升 |
| **D** | 上下文工程（缓存 + 增量） | L5 | P0 | 中 | ✅ 成本降低 + 响应加快 |
| **A** | 开发防错体系 | 横切 | P1 | 中 | ❌ 开发者工具 |
| **C** | 一致性免疫增强 | L3 | P1 | 中 | ✅ 误报减少 |
| **E** | 记忆系统增强 | L5/L6 | P1 | 中 | ✅ 长篇小说上下文更好 |
| **G** | 类型驱动工程实践 | 横切 | P1 | 中 | ❌ 开发者工具 |
| **H** | 发布与质量体系 | 横切 | P1 | 中 | ❌ 开发者工具 |
| **B** | 创作引擎优化（可选多 Agent） | L2 | P2 | 高 | ✅ 高级功能 |

---

## A. 开发防错体系（横切 L0-L7）

> 参考: AI开发防错设计大全（78 个项目最佳实践）
> 适用场景: 灵文是 AI 辅助开发项目，AI 协作者可能破坏架构不变量
> 映射: 横切 L0-L7，主要保护 L0 故事契约和 L3 免疫层不变量

### A.1 防线一览（精简为 5 道）

| 防线 | 描述 | 当前状态 | 目标 |
|------|------|----------|------|
| 1. AGENTS.md 架构契约 | 编码架构不变量和多文件修改链路 | ❌ 无 | ✅ 创建 |
| 2. 类型系统约束 | 禁用类型逃逸出口 | ⚠️ 部分 | ✅ 全开 strict + 禁 as any |
| 3. 守卫测试 | 包边界、Composable 导出完整性 | ❌ 无 | ✅ 5 个守卫测试 |
| 4. 错误分类系统 | 显式异常类 + fail-fast | ⚠️ 部分 | ✅ 90%+ 覆盖率 |
| 5. 供应链安全 | 精确锁版 + 依赖变更纪律 | ⚠️ 基础 | ✅ 精确锁版 |

### A.2 防线 1: AGENTS.md 架构契约

```markdown
# LingWen 项目 AI 协作契约

## 架构不变量（不可违反）
1. infra/ 与 dashboard/ 单向依赖 — dashboard 可依赖 infra，infra 禁止依赖 dashboard
2. L3 一致性层为纯函数核心 — 检查器 = 规则引擎，LLM Enhanced = AI 增强，互不混用
3. 创作流不可中断 — 任何章节生产管线必须支持 checkpoint 恢复
4. 涟漪修改必须审计留存 — 跨卷修改必须记录审计日志，支持回滚
5. 成本预算硬上限 — 单卷 AI 调用成本超过预算时阻断，需人工确认
6. 免疫侧禁止逆向依赖创作侧 — L3/L4 绝不引用 L2 任何模块

## 多文件修改链路（改一处必须同步改 N 处）
- 新增检查器: consistency/checkers/ + engine/checker_inspector.py + tests/
- 新增 API 端点: dashboard/routes/ + dashboard/models/ + frontend/src/api/ + tests/
- 新增 Composable: frontend/src/composables/ + tests/ + composables/index.js
- 新增 Pinia Store: frontend/src/stores/ + tests/ + stores/index.js
- 改 DB schema: persistence/schemas.py + state/database.py + tests/

## Do-Not-Delete 清单
- infra/persistence/registry.py（单例注册表，多模块依赖）
- infra/state/state_manager.py（状态机，创作流恢复依赖）
- dashboard/frontend/src/utils/asyncStoreUtils.js（异步生命周期管理）

## 反模式清单
- 禁 `as any`、`@ts-ignore`、`@ts-nocheck`
- 禁空 catch 块（必须记录日志或 rethrow）
- 禁删除 Failing Test
- 禁 `git add -A`（只 stage 自己改的文件）
- 禁未经请求的依赖升级
- 改 schema/API 必须同步四层: db → types → handler → ui

## 提交纪律
- 未验证的修改 commit 为 WIP
- PR 必须包含运行证据（测试输出 / 截图）
- NO EVIDENCE FILE == NO COMMIT
```

### A.3 防线 2: 类型系统强化

**TypeScript 侧**:
```json
{
  "strict": true,
  "noImplicitAny": true,
  "noImplicitReturns": true,
  "noUnusedLocals": true,
  "strictNullChecks": true,
  "noFallthroughCasesInSwitch": true
}
```

**ESLint 新增**:
```javascript
{
  '@typescript-eslint/no-explicit-any': 'error',
  '@typescript-eslint/ban-ts-comment': ['error', {
    'ts-ignore': true, 'ts-nocheck': true, 'ts-expect-error': true
  }]
}
```

**Python 侧**:
```toml
[tool.mypy]
strict = true
disallow_untyped_defs = true
warn_return_any = true
```

### A.4 防线 3: 守卫测试

```typescript
// tests/guards/no-reverse-dependency.spec.ts
// 守护 L3/L4 不依赖 L2 的铁律
test('L3 一致性层不得导入 L2 创作引擎模块', () => { ... });

// tests/guards/composable-barrel.spec.ts
// 守护 Composable 导出完整性
test('composables/index.js 必须导出所有 composable', () => { ... });
```

### A.5 防线 4: 错误分类系统

```python
class LingWenError(Exception): ...
class ValidationError(LingWenError): ...    # 参数校验失败
class LLMError(LingWenError): ...           # LLM 调用失败
class ConsistencyError(LingWenError): ...   # 一致性检查失败
class RippleError(LingWenError): ...        # 涟漪异常
class BudgetError(LingWenError): ...        # 预算超支
class ConfigError(LingWenError): ...        # 配置错误

# 原则
# Critical path: fail-fast（throw），禁止静默吞掉
# Non-critical path: fail-open（log + 继续）
# 错误必须携带修复建议
```

---

## B. L2 创作引擎优化

> 映射: L2 创作引擎层
> 现有基础: MasterController + 5 种章节生产管线 + MC 写作/编辑/工作流
> 策略: 增强现有单 Agent 架构，多 Agent 为可选高级模式

### B.1 现状与问题

当前是单 Agent 架构（MasterController 做所有决策），已有成熟的：
- 章节生产管线（pilot/batch/retry/outline/golden_path）
- 写作/编辑/工作流模块
- 决策队列管理

**核心问题**: 不是缺少多 Agent，而是上下文构建和 AI 调用效率需要优化。

### B.2 优化方案: 增强 MasterController + 可选多 Agent

**默认模式**: 增强单 Agent（保持现有架构，优化上下文和缓存）

```
MasterController 增强:
├── 上下文构建（见 D 章节）
├── 记忆注入（见 E 章节）
├── 成本感知路由（已有 TieredRouter，增强预算预检）
└── 创作决策（现有逻辑，增加 checkpoint 粒度）
```

**可选高级模式**: 多 Agent 协作（用户手动开启，成本提示）

```
用户选择"深度质量模式"时启动:
├── 大纲审核 Agent: 检查大纲是否符合故事契约
├── 角色一致性 Agent: 检查新出场角色设定
├── 质量审查 Agent: 完整质量检查
└── 结果汇总 → 人工决策
```

**成本控制**:
- 高级模式启动前显示预估成本
- 每个 Agent 最大调用次数限制（默认 3 次）
- 总成本超预算自动降级为单 Agent 模式

### B.3 迁移策略

| 步骤 | 类型 | 说明 |
|------|------|------|
| 1. 增强 MasterController | 改造 | 在现有文件上增加上下文缓存和预算预检 |
| 2. 增加 checkpoint 粒度 | 改造 | 章节生产管线增加更细粒度的恢复点 |
| 3. 可选多 Agent | 增量 | 新增 agent_system/agents/ 子目录，不影响现有逻辑 |
| 4. 成本提示 UI | 增量 | 前端新增成本预估组件 |

---

## C. L3 一致性免疫增强

> 映射: L3 一致性免疫层
> 现有基础: 20+ 规则检查器、7 LLM 增强检查器、9 修复器、仲裁器
> 策略: 优化误报率 + 创意豁免白名单 + 检查器性能基线

### C.1 优化方案

**1. 误报率优化**
- 建立误报反馈机制：用户可标记"这不是问题"
- 统计每个检查器的误报率
- 误报率 > 20% 的检查器进入优化队列

**2. 创意豁免白名单**
- 用户可声明"本章节为创意实验，降低检查强度"
- 白名单模式下：钻石级检查保留，黄金/白银级降级为建议
- 白名单章节标记，后续涟漪扫描时标注"创意豁免区"

**3. 检查器性能基线**
```json
{
  "character_checker": { "max_ms": 500, "current_ms": 120 },
  "timeline_checker": { "max_ms": 300, "current_ms": 80 },
  "foreshadow_checker": { "max_ms": 800, "current_ms": 350 },
  "llm_enhanced_checkers": { "max_total_ms": 5000, "current_ms": 2800 }
}
```

**4. AI Tells 黑名单集成**
- 将 taste-skill 的 AI Tells 黑名单集成到 AiGlossChecker
- 检测 AI 生成文本的套路化表达
- 提供风格多样性评分

### C.2 迁移策略

| 步骤 | 类型 | 说明 |
|------|------|------|
| 1. 误报反馈机制 | 增量 | 新增 feedback 端点 + 前端反馈按钮 |
| 2. 创意豁免白名单 | 增量 | whitelist_manager.py 扩展 + 前端开关 |
| 3. 性能基线 | 增量 | 新增 tests/baselines/checker-performance.json |
| 4. AI Tells 集成 | 改造 | AiGlossChecker 扩展 |

---

## D. L5 AI 编排与上下文工程

> 映射: L5 AI 编排层
> 现有基础: ContextBuilder + PromptTemplates + ChapterMemoryHook + WorldModelEngine
> 策略: 增加缓存层、增量构建、上下文压缩，降低 AI 调用成本

### D.1 当前问题

每次 AI 调用都重新构建完整上下文（故事契约 + 世界观 + 人物设定 + 章节历史），即使 90% 内容未变化。

### D.2 优化方案: 三层缓存 + 增量构建

```
上下文构建流程（优化后）:

┌─────────────────────────────────────────────┐
│  Layer 1: 永久缓存（故事契约 + 世界观设定）  │
│  构建一次，哈希校验，仅变更时重建            │
│  预计节省: 每次调用 ~2000 tokens             │
├─────────────────────────────────────────────┤
│  Layer 2: 卷级缓存（当前卷大纲 + 人物状态）  │
│  卷切换时重建，卷内复用                      │
│  预计节省: 每次调用 ~1500 tokens             │
├─────────────────────────────────────────────┤
│  Layer 3: 章节级增量（当前章节上下文）       │
│  每次调用追加最新章节内容                    │
│  不可缓存，但可增量构建                      │
├─────────────────────────────────────────────┤
│  Layer 4: 用户输入（turn 级，不可缓存）      │
└─────────────────────────────────────────────┘
```

### D.3 缓存意识 Prompt 排列

```
系统 Prompt 排列规则:
1. 故事契约（永久不变）→ 缓存 prefix
2. 世界观设定（半永久）→ 缓存 prefix
3. 人物设定（半永久）→ 缓存 prefix
4. 当前卷大纲（卷级）→ 缓存 prefix
5. 当前章节历史（章节级）→ 不缓存，最后 append
6. 用户最新输入（turn 级）→ 不缓存，最后 append

原则: 缓存内容放前面，变动内容放最后
```

### D.4 上下文压缩（长篇小说场景）

```
当上下文超过 token 限制时，启用压缩策略:
- head 50%: 保留开头（故事背景 + 核心人物设定）
- tail 40%: 保留结尾（最近 3 章 + 用户输入）
- middle 10%: 摘要替代（中间章节用 TL;DR）
- 伏笔状态: 始终保留未回收伏笔列表（不压缩）
```

### D.5 迁移策略

| 步骤 | 类型 | 说明 |
|------|------|------|
| 1. 缓存层实现 | 增量 | 新增 prompt_engineering/cache.py |
| 2. ContextBuilder 改造 | 改造 | 集成缓存层，保持现有接口不变 |
| 3. 压缩策略 | 增量 | 新增 prompt_engineering/compressor.py |
| 4. 性能验证 | 测试 | 对比缓存前后的 token 消耗 |

---

## E. L5/L6 记忆系统增强

> 映射: L5 AI 编排 + L6 持久化
> 现有基础: ChapterMemoryHook + world_model/（8 文件）+ memory_system/
> 策略: 基于现有 world_model 增强，不引入向量库

### E.1 优化方案: 基于 world_model 的三级记忆

```
工作记忆 (Working Memory):
- 基于: ChapterMemoryHook（已有）
- 内容: 当前章节上下文 + 用户输入 + AI 生成内容
- 增强: 无需改变，已满足需求

短期记忆 (Short-term Memory):
- 基于: world_model/（已有）
- 内容: 当前卷上下文 + 人物状态 + 伏笔状态 + 事件因果
- 增强: 增加"伏笔状态快照"（当前卷未回收伏笔列表）
- 增强: 增加"人物状态快照"（当前卷人物属性变更记录）

长期记忆 (Long-term Memory):
- 基于: persistence/ + story_contracts/（已有）
- 内容: 人物档案 + 世界设定 + 故事契约 + 创作模式
- 增强: 增加"创作模式库"（记录成功/失败的创作策略）
- 不引入向量库: 小说世界观是结构化数据，SQLite 足够
```

### E.2 记忆提取与注入（优化后）

```
创作前:
1. 加载故事契约（长期记忆，persistence/）
2. 加载当前卷上下文（短期记忆，world_model/）
3. 加载伏笔状态快照（短期记忆，新增）
4. 加载人物状态快照（短期记忆，新增）
5. 注入工作记忆（ChapterMemoryHook，已有）

创作中:
6. 实时更新工作记忆（已有）
7. 检测关键事件（伏笔埋设/回收、人物状态变更）

创作后:
8. 更新 world_model 快照（已有，增强增量更新）
9. 更新故事契约（如有变更，人工审核）
10. 记录创作模式（新增，用于 L7 进化）
```

### E.3 迁移策略

| 步骤 | 类型 | 说明 |
|------|------|------|
| 1. 伏笔状态快照 | 增量 | world_model/ 新增 foreshadow_snapshot.py |
| 2. 人物状态快照 | 增量 | world_model/ 新增 character_snapshot.py |
| 3. 创作模式库 | 增量 | persistence/ 新增创作模式表 |
| 4. ChapterMemoryHook 增强 | 改造 | 集成快照数据 |

---

## F. L1 前端架构优化

> 映射: L1 接入与呈现层
> 现有基础: 13 页面、40+ Composables、4 Pinia Store
> 策略: 拆分超大 Composable + 完成 JS→TS 迁移

### F.1 useCreatorWriteWorkbench 拆分

```
当前: useCreatorWriteWorkbench.ts (49 字段)
↓
拆分后:
├── useCreatorWriteWorkbench.ts (保留，作为聚合入口，约 15 字段)
├── useWorkbenchSelection.ts (新增，选区管理，~8 字段)
├── useWorkbenchCheckpoint.ts (新增，检查点管理，~10 字段)
├── useWorkbenchDiff.ts (新增，差异对比，~8 字段)
└── useWorkbenchExport.ts (新增，导出管理，~8 字段)
```

### F.2 剩余 JS→TS 迁移

已完成 10+ 核心 Composable 的 TS 迁移。剩余约 30 个 .js Composable 中：
- 高频使用（8 个）→ 优先迁移
- 低频使用（15 个）→ 渐进迁移，添加 JSDoc 过渡
- 工具类（7 个）→ 保持 .js + JSDoc（改动成本低，风险低）

### F.3 迁移策略

| 步骤 | 类型 | 说明 |
|------|------|------|
| 1. useCreatorWriteWorkbench 拆分 | 改造 | 拆分为 4 子模块 + 1 聚合入口 |
| 2. 高频 Composable TS 迁移 | 改造 | 8 个文件逐个迁移 |
| 3. 前端测试更新 | 改造 | 同步更新测试文件 |
| 4. 验证 | 测试 | vue-tsc + vitest 全量通过 |

---

## G. 类型驱动工程实践（横切）

> 参考: codewhale、openhands、oh-my-claudecode
> 映射: 横切 L1-L7

### G.1 Branded Type（防止 ID 混淆）

```typescript
type ChapterId = string & { readonly __brand: "ChapterId" };
type VolumeId = string & { readonly __brand: "VolumeId" };
type CharacterId = string & { readonly __brand: "CharacterId" };

// 编译期防止 AI 把 ChapterId 当 VolumeId 用
function getChapter(id: ChapterId): Chapter { ... }
function getVolume(id: VolumeId): Volume { ... }
```

### G.2 判别联合（类型拒绝非法状态）

```typescript
type CheckResult =
  | { kind: "pass"; checker: string }
  | { kind: "fail"; checker: string; findings: Finding[] }
  | { kind: "error"; checker: string; error: Error }
  | { kind: "skipped"; checker: string; reason: string };

// 调用方必须处理所有 4 种情况
switch (result.kind) {
  case "pass": ...
  case "fail": ...
  case "error": ...
  case "skipped": ...
}
```

### G.3 迁移策略

| 步骤 | 类型 | 说明 |
|------|------|------|
| 1. Branded Type 定义 | 增量 | types/ 新增 branded.ts |
| 2. 核心 API 改造 | 改造 | 章节/卷/人物 API 使用 Branded Type |
| 3. 判别联合推广 | 改造 | CheckResult、ProductionEvent 等 |

---

## H. 发布与质量体系

### H.1 证据驱动 QA

```
创作完成
  → 自动运行检查矩阵（20+ 检查器）
  → 生成证据文件:
      ├── check_report.json（检查报告）
      ├── fix_log.txt（修复日志）
      └── cost_summary.json（成本摘要）
  → 证据文件缺失 → 阻断发布
```

### H.2 写审分离（可选，高级质量模式）

```
用户选择"质量审查"时:
1. Author pass: 创作 Agent 生成章节
2. Reviewer pass: 审查 Agent（新 session）独立审查
   - 不传 Author 的 CLAIM（防确认偏误）
   - 3 cycle 上限 + STOP 条件
```

### H.3 回归基线

```json
{
  "checker_coverage": { "min": 0.80 },
  "checker_performance": { "max_total_ms": 10000 },
  "ripple_accuracy": { "min_precision": 0.85, "min_recall": 0.80 },
  "ai_cost_budget": { "per_volume_max_usd": 5.0, "per_chapter_max_usd": 0.5 },
  "checker_false_positive_rate": { "max": 0.20 },
  "test_pass_rate": { "min": 1.0 }
}
```

---

## 明确不做清单

### 不做的事情及原因

| 不做 | 原因 |
|------|------|
| **MCP 协议标准化** | 灵文是独立应用，内部工具调用不需要跨工具互操作。声明式工具注册足够 |
| **六阶段权限评估流水线** | 为代码执行沙箱设计（claw-code），创作场景不需要 |
| **三平台沙箱隔离** | 代码执行场景（openinterpreter），不适用于创作 |
| **默认多 Agent Squad** | 成本爆炸（8x AI 调用），与"成本即边界"铁律矛盾 |
| **三方辩论模式** | 每个争议 4x LLM 调用，成本过高 |
| **向量库长期记忆** | 小说世界观是结构化数据，SQLite + world_model 更合适 |
| **ReactFlow DAG 工作流编辑器** | 超出用户需求，增加 UI 复杂度 |
| **代码生成管线（codegen）** | 灵文不生成代码，不适用 |
| **用户行为埋点分析** | 隐私风险，当前阶段不需要 |
| **WebSocket 替换为 SSE** | 现有 WebSocket 双通道已稳定，无需替换 |

---

## 实施路线图（含迁移策略）

### Phase 1: 创作体验优化（P0，2-3 周）

| 任务 | 层级 | 类型 | 迁移策略 |
|------|------|------|----------|
| 1.1 useCreatorWriteWorkbench 拆分 | L1 | 改造 | 拆分子模块 + 聚合入口，保持对外接口兼容 |
| 1.2 上下文缓存层 | L5 | 增量 | 新增 cache.py，ContextBuilder 集成，不破坏现有接口 |
| 1.3 上下文压缩 | L5 | 增量 | 新增 compressor.py，仅超 token 限制时触发 |
| 1.4 高频 Composable TS 迁移 | L1 | 改造 | 8 个文件逐个迁移，同步更新测试 |

**验证标准**: vitest 918 测试全部通过 + vue-tsc 零错误

### Phase 2: 质量与防错（P1，3-4 周）

| 任务 | 层级 | 类型 | 迁移策略 |
|------|------|------|----------|
| 2.1 AGENTS.md 创建 | 横切 | 增量 | 新增文件，不影响代码 |
| 2.2 类型系统强化 | 横切 | 改造 | tsconfig.json + eslint.config.js 修改 |
| 2.3 守卫测试 | 横切 | 增量 | 新增 tests/guards/ 目录 |
| 2.4 错误分类系统 | 横切 | 改造 | 新增 errors.py，逐步替换现有 Exception |
| 2.5 检查器误报率优化 | L3 | 增量 | 新增反馈机制 + 性能基线 |
| 2.6 创意豁免白名单 | L3 | 增量 | whitelist_manager.py 扩展 |
| 2.7 AI Tells 黑名单集成 | L3 | 改造 | AiGlossChecker 扩展 |
| 2.8 记忆系统增强 | L5/L6 | 增量 | world_model/ 新增快照模块 |

**验证标准**: 检查器误报率可度量 + 守卫测试通过

### Phase 3: 高级功能（P2，3-4 周）

| 任务 | 层级 | 类型 | 迁移策略 |
|------|------|------|----------|
| 3.1 可选多 Agent 模式 | L2 | 增量 | 新增 agents/ 子目录，默认关闭 |
| 3.2 写审分离 | 横切 | 增量 | 新增审查流程，默认关闭 |
| 3.3 Branded Type 推广 | 横切 | 改造 | 核心 API 逐步改造 |
| 3.4 回归基线自动化 | 横切 | 增量 | CI 集成基线检查 |

**验证标准**: 高级模式不影响默认模式性能 + 成本可控

---

## 关键指标目标

| 指标 | V2.0 基线 | V3.1 目标 | 衡量方式 | 备注 |
|------|-----------|-----------|----------|------|
| Vue 测试通过率 | 918/918 | 100% | vitest run | 不降低 |
| TypeScript 错误 | 0 | 0 | vue-tsc --noEmit | 不降低 |
| AGENTS.md | 无 | 已创建 | 文件存在 | 新增 |
| 类型逃逸出口 | 未封堵 | 0 个 | ESLint no-explicit-any: error | 新增规则 |
| 守卫测试 | 0 个 | 5 个 | tests/guards/ | 新增 |
| 错误分类覆盖率 | ~30% | 90%+ | 显式异常类使用率 | 提升 |
| Composable 平均字段 | ~15 | ≤10 | 代码复杂度 | 拆分后 |
| 上下文缓存命中率 | 0% | 70%+ | 缓存层日志 | 新增 |
| 检查器误报率 | 未度量 | ≤20% | 用户反馈统计 | 新增可度量 |
| AI 单章成本 | 未度量 | ≤$0.5 | cost_tracker | 新增可度量 |
| 依赖精确锁版 | 部分 | 100% | ==精确版本 | 提升 |

---

> **文档版本**: V3.1
> **生成日期**: 2026-07-30
> **参考来源**: 78 个 Agent 项目深度技术选型分析 + AI 开发防错设计大全
> **核心原则**: 在 V2.0 八层架构基础上增量优化，不推倒重来；复杂度封装在后端，UI 保持简洁；成本即边界，每个 AI 增强必须论证成本效益
> **状态**: 架构优化方案（待讨论）