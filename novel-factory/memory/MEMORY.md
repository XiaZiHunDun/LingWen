# 灵文 · 工业化小说生产系统 - 项目记忆

## 项目状态
- **项目路径**: `/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen`
- **当前版本**: v6.1 (优化完成版)
- **发布状态**: ✅ 已发布 (2026-05-18)
- **项目状态**: PHASE_7_CLOSE (归档闭环)
- **总章节数**: 360章
- **质量评级**: S级

## 目录结构
```
novel-factory/
├── ai_service/          # AI Provider 抽象层 (OpenAI/Anthropic)
├── consistency/        # 一致性检查引擎 (83 passed)
├── hooks/              # 事件钩子系统
├── quality_tools/      # 质量工具 (QualityGate/MultiStyleDrafter)
├── memory_system/      # 记忆系统 (218 passed)
├── 10_方法论/          # 方法论文档
├── tests/              # 测试套件 (553 passed)
└── docs/superpowers/   # 优化方向设计文档
```

## 审核维度 (S1-S8)
| 维度 | 说明 |
|------|------|
| S1 | 剧情完整性 |
| S2 | 逻辑自洽 |
| S3 | 文笔风格 |
| S4 | 情感共鸣 |
| S5 | 节奏控制 |
| S6 | 可读性 |
| S7 | 主角魅力 |
| S8 | 人物弧光 |

## 优化方向 (A-H 全部完成)
1. **AI服务抽象层** → `ai_service/` (OpenAI + Anthropic 多Provider)
2. **一致性检查** → `consistency/` (10+ 检测器)
3. **插件框架** → `hooks/` (YAML配置的事件驱动)
4. **质量工具** → `quality_tools/` (QualityGate + MultiStyleDrafter)
5. **Qdrant集成** → `memory_system/vector/` (LRU缓存、批量查询)
6. **版本管理** → `10_方法论/.../version_manager.py`
7. **模板推荐** → `10_方法论/.../template_recommender.py`
8. **伏笔追踪** → `consistency/checkers/foreshadow_checker.py`

## 测试覆盖
- **总测试**: 553 passed, 2 skipped
- **memory_system**: 218 passed
- **consistency**: 83 passed
- **prompt_system**: 52 passed
- **ai_service**: 17 passed
- **hooks**: 12+ passed
- **quality_tools**: 50+ passed

## 核心文件
- `workflow_state.json` - 状态机文件
- `novel-factory/CLAUDE.md` - 主控调度Agent定义
- `docs/superpowers/` - 设计文档和实施计划

---
→ See debugging.md (问题解决记录)
→ See patterns.md (项目模式与约定)