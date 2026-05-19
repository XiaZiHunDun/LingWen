# 实施路线图：小说工厂优化方向

> **版本**: v1.0
> **日期**: 2026-05-19
> **状态**: 已整合（原30+文档合并为8个方向）
> **优先级**: P1-P2

---

## 1. 整合概览

### 1.1 最终优化方向（8个）

```
┌─────────────────────────────────────────────────────────────────┐
│                    小说工厂优化方向                              │
├───────┬────────────────────────────────────┬─────────┬─────────┤
│ 方向  │ 名称                               │ 优先级  │ 状态    │
├───────┼────────────────────────────────────┼─────────┼─────────┤
│  A    │ 整合记忆系统                       │   P1    │ 新设计  │
│  B    │ 整合Agent协作系统                  │   P1    │ 新设计  │
│  C    │ 整合提示词体系                     │   P1    │ 新设计  │
│  D    │ 整合一致性保障系统                 │   P1    │ 新设计  │
│  E    │ 伏笔追踪系统（独立）               │   P1    │ 新设计  │
│  F    │ 整合AI服务抽象层                   │   P2    │ 新设计  │
│  G    │ 整合插件框架                       │   P2    │ 新设计  │
│  H    │ 整合质量工具集                     │   P2-P3 │ 新设计  │
└───────┴────────────────────────────────────┴─────────┴─────────┘
```

### 1.2 依赖关系图

```
                    ┌─────────────────┐
                    │    记忆系统 A    │
                    │  (P1, 先行基础)  │
                    └────────┬────────┘
                             │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
   │ Agent协作 B │   │ 一致性保障 D│   │ 伏笔追踪 E  │
   │   (P1)     │   │    (P1)     │   │    (P1)     │
   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
          │                 │                 │
          └────────┬────────┴────────┬────────┘
                   ▼                 │
          ┌─────────────────┐         │
          │   提示词体系 C  │◄────────┘
          │     (P1)       │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │  AI服务抽象层 F │
          │      (P2)       │
          └────────┬────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
   ┌─────────────┐   ┌─────────────┐
   │  插件框架 G │   │ 质量工具 H  │
   │    (P2)     │   │   (P2-P3)   │
   └─────────────┘   └─────────────┘
```

---

## 2. 实施阶段

### Phase 1：核心基础设施（1-4周）

| 方向 | 任务 | 交付物 | 验收标准 |
|------|------|--------|---------|
| **A** | Docker启动Qdrant | Qdrant容器 | Qdrant UI可访问 |
| **A** | 实现MemoryGateway | memory_gateway.py | 统一入口可用 |
| **A** | 实现三层索引结构 | collections_schema.yaml | Schema完整 |
| **A** | 批量嵌入现有章节 | embed_chapters.py | 360章全部嵌入 |
| **A** | 与记忆系统集成 | 集成代码 | 上下文获取正常 |
| **A** | 验收测试 | 测试报告 | 功能正常 |

**阶段产出**：记忆系统v1.0，可提供上下文推送和主动查询

---

### Phase 2：核心功能系统（5-10周）

| 方向 | 任务 | 交付物 | 验收标准 |
|------|------|--------|---------|
| **B** | 创建5个专项Agent | agent_profile + tools | Agent可用 |
| **B** | 实现社交模拟引擎 | social_engine | 关系追踪正常 |
| **B** | 实现上下文构建器 | context_builder.py | 数据共享正常 |
| **B** | 实现主控调度器 | master_controller.py | 任务编排正常 |
| **C** | 创建CARE模板结构 | 目录+索引 | 结构完整 |
| **C** | 实现场景温度映射 | 场景温度映射.yaml | 映射合理 |
| **C** | 实现版本管理工具 | 版本工具 | 支持历史回滚 |
| **D** | 实现一致性引擎 | consistency_engine.py | 引擎可用 |
| **D** | 实现8个检查器 | checkers/*.py | 检查正常 |
| **D** | 实现实时检查 | realtime_check | 预警实时 |
| **E** | 创建伏笔登记SOP | 伏笔登记流程 | 流程可执行 |
| **E** | 实现伏笔分析报告 | 分析报告模板 | 报告完整 |

**阶段产出**：
- Agent协作系统v1.0，5个专项Agent可协作
- 提示词体系v1.0，CARE模板可用
- 一致性保障系统v1.0，8维度检查
- 伏笔追踪系统v1.0，登记-追踪-报告

---

### Phase 3：增强与集成（11-16周）

| 方向 | 任务 | 交付物 | 验收标准 |
|------|------|--------|---------|
| **F** | 实现AIGateway | gateway.py | 统一接口可用 |
| **F** | 实现模型适配器 | adapters/*.py | 多Provider支持 |
| **F** | 实现熔断降级 | circuit_breaker.py | 故障切换正常 |
| **F** | 实现成本优化 | cost_optimizer.py | 成本统计正常 |
| **G** | 实现插件管理器 | plugin_manager.py | 插件管理可用 |
| **G** | 实现沙箱隔离 | sandbox.py | 隔离有效 |
| **G** | 开发核心插件 | core_plugins/* | 插件功能正常 |
| **H** | 实现卡文突破工具 | writer_block_toolkit | 突破功能正常 |
| **H** | 实现章纲扩展工具 | chapter_expansion_toolkit | 扩展功能正常 |
| **H** | 实现AI拆书工具 | book_analysis_toolkit | 拆书功能正常 |

**阶段产出**：
- AI服务抽象层v1.0，多Provider无缝切换
- 插件框架v1.0，标准化接口+沙箱隔离
- 质量工具集v1.0，辅助写作工具完备

---

### Phase 4：优化与迭代（17-20周）

| 方向 | 任务 | 交付物 | 验收标准 |
|------|------|--------|---------|
| **A** | 性能优化 | 优化报告 | 响应时间 < 2秒 |
| **B** | 端到端测试 | 测试报告 | 完整流程正常 |
| **C** | 模板推荐引擎 | 推荐系统 | 场景推荐准确 |
| **D** | 与记忆系统深度集成 | 集成代码 | 状态同步正常 |
| **E** | 预警机制优化 | 预警系统 | 超期自动提醒 |
| **F** | 缓存命中率优化 | 优化报告 | 命中率 ≥ 30% |
| **G** | 插件商店 | plugin_store | 可浏览 |
| **H** | 持续迭代 | 优化流程 | 基于数据迭代 |

---

## 3. 优先级矩阵

```
            重要性
            高     低
          ┌──────┬──────┐
      高  │  A   │  E   │
  影响   ├──────┼──────┤
      低  │  B   │  F   │
          │  C   │  G   │
          │  D   │  H   │
          └──────┴──────┘
```

### 决策解读

| 区域 | 方向 | 策略 |
|------|------|------|
| 高重要×高影响 | A, B, C, D, E | **立即启动**，并行开发 |
| 高重要×低影响 | E | **第二个启动** |
| 低重要×高影响 | F, G | **第三个启动** |
| 低重要×低影响 | H | **按需启用** |

---

## 4. 并行开发策略

### 第一批并行（P1方向）

```
[记忆系统 A] ─────────────────────────────┐
                                          │
[Agent协作 B] ──────┐                      │
                    ├──► [提示词体系 C] ──┤
[一致性保障 D] ─────┘                      │
                                          │
[伏笔追踪 E] ─────────────────────────────┘
```

### 第二批并行（P2方向）

```
[AI服务抽象层 F] ←── [提示词体系 C]
                              │
[插件框架 G] ────────────────┤
                              │
[质量工具 H] ◄───────────────┘
```

---

## 5. 归档的原始文档

### 归档到 deprecated/ 的文档（29个）

#### Specs（归档11个）
- 2026-05-19-rag-memory-system-design.md
- 2026-05-19-multi-agent-social-simulation-design.md
- 2026-05-19-care-prompt-framework-design.md
- 2026-05-19-foreshadow-tracking-system-design.md
- 2026-05-19-character-consistency-check-design.md
- 2026-05-19-ai-service-abstraction-layer-design.md
- 2026-05-19-pacing-visualization-design.md
- 2026-05-19-temperature-guidance-design.md
- 2026-05-19-react-architecture-design.md
- 2026-05-19-rag-support-design.md
- 2026-05-19-plugin-system-design.md

#### Plans（归档18个）
- 2026-05-19-vector-memory-system.md
- 2026-05-19-multi-agent-collaboration.md
- 2026-05-19-schema-cards.md
- 2026-05-19-consistency-audit.md
- 2026-05-19-style-unification.md
- 2026-05-19-model-tier-strategy.md
- 2026-05-19-data-loop.md
- 2026-05-19-relationship-graph.md
- 2026-05-19-prompt-template-library.md
- 2026-05-19-version-control.md
- 2026-05-19-care-prompt-framework-implementation-plan.md
- 2026-05-19-foreshadow-tracking-implementation-plan.md
- 2026-05-19-character-consistency-check-implementation-plan.md
- 2026-05-19-ai-service-abstraction-layer-implementation-plan.md
- 2026-05-19-pacing-visualization-implementation-plan.md
- 2026-05-19-temperature-guidance-implementation-plan.md
- 2026-05-19-react-architecture-implementation-plan.md
- 2026-05-19-rag-support-implementation-plan.md
- 2026-05-19-plugin-system-implementation-plan.md

---

## 6. 最终设计文档清单

### 整合后的Spec（8个）

```
docs/superpowers/specs/
├── 2026-05-19-integrated-memory-system-design.md      # 方向A
├── 2026-05-19-integrated-agent-system-design.md       # 方向B
├── 2026-05-19-integrated-prompt-system-design.md      # 方向C
├── 2026-05-19-integrated-consistency-system-design.md # 方向D
├── 2026-05-19-foreshadow-tracking-system-design.md     # 方向E
├── 2026-05-19-integrated-ai-gateway-design.md        # 方向F
├── 2026-05-19-integrated-plugin-framework-design.md   # 方向G
├── 2026-05-19-integrated-quality-tools-design.md      # 方向H
└── deprecated/                                          # 归档目录
```

### 下一步：实现计划

每个方向需要从Spec生成Implementation Plan，优先级顺序：

1. **记忆系统A** → 生成实现计划
2. **Agent协作系统B** → 生成实现计划
3. **提示词体系C** → 生成实现计划
4. **一致性保障D** → 生成实现计划
5. **伏笔追踪E** → 生成实现计划
6. **AI服务抽象层F** → 生成实现计划
7. **插件框架G** → 生成实现计划
8. **质量工具H** → 生成实现计划

---

## 7. 关键里程碑

| 时间 | 里程碑 | 产出 |
|------|--------|------|
| 第4周 | Phase 1完成 | 记忆系统v1.0 |
| 第10周 | Phase 2完成 | Agent+提示词+一致性+伏笔 |
| 第16周 | Phase 3完成 | AI抽象+插件+工具 |
| 第20周 | Phase 4完成 | 全部优化方向v1.0 |