# 提示词模板库

> 统一的小说写作提示词管理系统，基于 CARE 框架（Context-Action-Result-Example）

## 目录结构

```
提示词模板库/
├── README.md                           # 本文件
├── 00_模板索引.yaml                     # 模板索引清单
├── 01_大纲生成/                        # 大纲生成类模板
│   ├── 全文大纲_CARE.md
│   └── 卷大纲_CARE.md
├── 02_正文续写/                        # 正文续写类模板
│   ├── 标准续写_CARE.md
│   ├── 高潮场景_CARE.md
│   └── 对话场景_CARE.md
├── 03_描写增强/                        # 描写增强类模板
│   ├── 五感描写_CARE.md
│   └── 隐喻描写_CARE.md
├── 04_审核辅助/                        # 审核辅助类模板
│   ├── 逻辑检查_CARE.md
│   └── 角色一致性_CARE.md
├── 05_润色修改/                        # 润色修改类模板
│   ├── 语言润色_CARE.md
│   └── 情感强化_CARE.md
├── config/
│   └── prompts/
│       ├── 模板元数据Schema.yaml        # 模板元数据结构定义
│       ├── 场景温度映射.yaml            # 场景-温度参数映射
│       └── 风格指南库/                  # 风格配置
│           ├── 玄幻风格.yaml
│           └── 都市风格.yaml
└── prompt_assembler.py                 # 模板组装工具
```

## CARE 框架

所有模板遵循 CARE 四要素结构：

| 要素 | 说明 | 必须包含 |
|------|------|---------|
| **C** - Context | 背景 | 世界观、项目信息、当前状态 |
| **A** - Action | 行动 | 输出类型、约束条件、禁止项 |
| **R** - Result | 结果 | 质量指标(S1-S8)、字数要求 |
| **E** - Example | 示例 | 高质量示例、风格对照 |

## 模板分类

| 分类 | 用途 | 典型温度 |
|------|------|---------|
| `outline` 大纲生成 | 生成各类大纲 | 0.5-0.7 |
| `continuation` 正文续写 | 章节内容续写 | 0.6-0.8 |
| `description` 描写增强 | 五感、隐喻等增强 | 0.6-0.7 |
| `review` 审核辅助 | 逻辑、一致性检查 | 0.3-0.5 |
| `polish` 润色修改 | 语言、情感优化 | 0.3-0.5 |

## 温度选择指南

- **高温度 (0.75-0.9)**：创意头脑风暴、情节转折
- **中温度 (0.6-0.7)**：标准续写、大纲生成
- **低温度 (0.3-0.5)**：审核、润色、逻辑检查

详细映射见 `config/prompts/场景温度映射.yaml`

## 使用方式

### Python API

```python
from prompt_assembler import PromptAssembler

assembler = PromptAssembler("config/prompts")
prompt = assembler.assemble(
    template_name="标准续写",
    context={
        "world_setting": "...",
        "character_status": "...",
        "scene_location": "..."
    },
    temperature=0.7
)
```

### 模板组装工具

```bash
python prompt_assembler.py --template 标准续写 --input context.yaml --temp 0.7 --output prompt.txt
```

## 版本管理

模板版本格式：`v{MAJOR}.{MINOR}.{PATCH}`
- MAJOR：不兼容的重大变更
- MINOR：向后兼容的功能新增
- PATCH：向后兼容的问题修复

状态标签：`draft` | `active` | `deprecated`

## 与其他系统集成

- **记忆系统**：自动注入角色状态、伏笔状态
- **AI服务**：通过 AIGateway 调用，指定场景对应模型
- **Agent系统**：大纲师→大纲模板，写手→正文模板，审计官→审核模板