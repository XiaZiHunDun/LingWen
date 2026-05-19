# 作家部门提示词模板索引

> 版本：1.0 | 更新：2026-05-19

## 概述

作家部门提示词模板位于 `.claude/prompts/writer/` 目录，为作家提供标准化的写作指导。

---

## 模板列表

| 模板文件 | 用途 | Token估算 |
|----------|------|-----------|
| `chapter-writing-prompt.md` | 章节正文写作 | ~2000-2500 |
| `scene-description-prompt.md` | 场景/环境描写 | ~1200-1800 |
| `dialogue-generation-prompt.md` | 对话生成 | ~1500-2000 |
| `chapter-revision-prompt.md` | 章节修改指导 | ~1000-1500 |

---

## 使用方式

### 1. 直接加载模板

读取对应模板文件，替换占位符后使用。

### 2. 占位符替换规则

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{novel_title}` | 作品名称 | 《星陨纪元》 |
| `{chapter_number}` | 章节号 | 025 |
| `{word_count}` | 目标字数 | 3000 |
| `{genre}` | 作品类型 | 玄幻 |
| 其他 | 见各模板内说明 | - |

### 3. 生成完整Prompt示例

```python
def generate_chapter_prompt(
    novel_title: str,
    chapter_number: int,
    chapter_type: str,
    context: dict
) -> str:
    template = read_template("chapter-writing-prompt.md")
    prompt = template.format(
        novel_title=novel_title,
        chapter_number=chapter_number,
        chapter_type=chapter_type,
        # ... 其他参数
    )
    return prompt
```

---

## 质量标准

所有作家部门提示词遵循以下标准：

1. **完整性**：包含角色、场景、情节、风格全部要素
2. **可执行性**：指导具体明确，作家可据此创作
3. **质量门控**：内置自评标准和检查点
4. **上下文关联**：与大纲、已有人物设定保持一致

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|---------|
| 2026-05-19 | 1.0 | 初始版本，创建4个核心模板 |