# 灵文 CLI 工具整合设计文档

> **版本**: v1.0
> **日期**: 2026-05-26
> **阶段**: Phase 1 - 工具整合

## 1. 概述

### 1.1 目标

创建统一的 CLI 入口 `lingwen.py`，整合现有的 35+ 个工具脚本，提供一致的操作界面和调用方式。

### 1.2 现状问题

- **工具分散**：质量检查、修复、验证工具各自独立
- **调用不统一**：参数格式不一致（`--chapters` vs `--start --end`）
- **重复代码**：多个工具包含相似的初始化和配置逻辑
- **难以追踪**：缺乏统一的执行状态管理

### 1.3 整合收益

- 单一入口降低学习成本
- 统一参数格式提高效率
- 共享配置减少代码重复
- 集中状态追踪便于监控

## 2. 设计方案

### 2.1 CLI 结构

```bash
lingwen.py <command> [options]

# 命令类别
lingwen.py check <range>      # 质量检查
lingwen.py repair <range>     # 批量修复
lingwen.py verify <range>     # 验证修复效果
lingwen.py status [chapter]   # 查看状态
lingwen.py doctor             # 系统诊断
```

### 2.2 统一参数格式

```bash
# 章节范围格式统一
--range 1-30          # 范围表示
--chapters 1,3,5     # 特定章节
--all                 # 所有章节

# 通用选项
--parallel N          # 并行数（默认4）
--verbose             # 详细输出
--dry-run             # 预览模式
```

### 2.3 命令详解

#### check - 质量检查

```bash
lingwen.py check 1-30 [options]

Options:
  --quick             # 快速检查（不含LLM）
  --full              # 完整检查（含LLM深度检查）
  --llm               # 仅LLM检查
  --report FILE       # 输出报告文件
```

**整合工具**：
- `quick_check.py` → `check --quick`
- `comprehensive_quality_check.py` → `check --full`
- `llm_quality_deep_check.py` → `check --llm`

#### repair - 批量修复

```bash
lingwen.py repair 1-30 [options]

Options:
  --track TYPE        # 修复类型（worldview/ai_trace/character/logic/all）
  --regression        # 修复后运行回归测试
  --parallel N        # 并行数
```

**整合工具**：
- `batch_repair.py` → `repair`
- `fix_worldview.py` → `repair --track worldview`
- `fix_ai_traces.py` → `repair --track ai_trace`
- `fix_character_consistency.py` → `repair --track character`

#### verify - 验证修复效果

```bash
lingwen.py verify 1-30 [options]

Options:
  --repaired          # 仅验证已修复章节
  --compare FILE      # 与备份对比
```

**整合工具**：
- `verify_quality.py` → `verify`
- `verify_repair_quality.py` → `verify --repaired`

#### status - 状态查看

```bash
lingwen.py status [chapter]

Options:
  --json              # JSON格式输出
  --summary           # 仅显示摘要
```

#### doctor - 系统诊断

```bash
lingwen.py doctor

Checks:
  - 环境配置完整性
  - 数据库连接状态
  - 章节文件完整性
  - 最新修复记录
```

## 3. 架构设计

### 3.1 目录结构

```
novel-factory/
├── lingwen.py                    # 统一CLI入口 (NEW)
├── infra/
│   └── cli/                      # CLI模块 (NEW)
│       ├── __init__.py
│       ├── commands.py            # 命令定义
│       ├── options.py             # 统一参数解析
│       ├── range_parser.py        # 范围解析器
│       └── output.py              # 输出格式化
├── tools/                        # 工具脚本（保持兼容）
│   ├── batch_repair.py
│   ├── verify_quality.py
│   └── ...
└── tools_legacy/                 # 旧工具备份 (RENAME)
    ├── quick_check.py
    ├── comprehensive_quality_check.py
    └── ...
```

### 3.2 核心组件

#### RangeParser

解析章节范围参数：

```python
class RangeParser:
    def parse("1-30") → List[int]
    def parse("1,3,5") → List[int]
    def parse("1-30,45,50-60") → List[int]
```

#### UnifiedOptions

统一选项定义：

```python
@dataclass
class UnifiedOptions:
    range: List[int]
    parallel: int = 4
    verbose: bool = False
    dry_run: bool = False
    output: Optional[Path] = None
```

#### CommandInterface

命令接口抽象：

```python
class Command:
    name: str
    description: str

    def add_options(self, parser)
    def execute(self, options) → int
```

## 4. 迁移策略

### 4.1 兼容性保持

- 旧工具保持运行能力（内部调用新CLI）
- 渐进式迁移：先保留旧工具，逐步转移

### 4.2 迁移步骤

1. 创建 `lingwen.py` 入口
2. 实现 `RangeParser` 和 `UnifiedOptions`
3. 实现 check 命令（整合 quick_check, comprehensive, llm）
4. 实现 repair 命令（整合 batch_repair 和 fix_* 工具）
5. 实现 verify 命令
6. 实现 status 和 doctor 命令
7. 将旧工具移动到 `tools_legacy/`

### 4.3 回滚方案

- 保留 `tools/` 中的原工具
- 迁移失败时可快速回退

## 5. 文件清单

### 5.1 新增文件

| 文件 | 行数 | 说明 |
|------|------|------|
| `lingwen.py` | ~150 | CLI入口 |
| `infra/cli/__init__.py` | ~20 | 模块导出 |
| `infra/cli/commands.py` | ~200 | 命令定义 |
| `infra/cli/options.py` | ~100 | 选项解析 |
| `infra/cli/range_parser.py` | ~80 | 范围解析 |
| `infra/cli/output.py` | ~60 | 输出格式化 |

### 5.2 迁移文件

| 原文件 | 目标位置 |
|--------|----------|
| `tools/quick_check.py` | `tools_legacy/` |
| `tools/comprehensive_quality_check.py` | `tools_legacy/` |
| `tools/batch_repair.py` | `tools_legacy/` |
| `tools/fix_*.py` | `tools_legacy/` |

## 6. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 迁移失败 | 工具不可用 | 保留旧工具，快速回退 |
| 参数不兼容 | 用户脚本失效 | 提供迁移指南 |
| 性能下降 | 检查变慢 | 保持并行优化 |

## 7. 成功标准

- [ ] `lingwen.py check 1-30 --quick` 正常运行
- [ ] `lingwen.py repair 1-30 --track worldview` 正常运行
- [ ] `lingwen.py verify 1-30` 正常运行
- [ ] `lingwen.py status` 显示正确状态
- [ ] `lingwen.py doctor` 诊断通过
- [ ] 所有现有测试继续通过
- [ ] 旧工具在 `tools_legacy/` 中保持可用
