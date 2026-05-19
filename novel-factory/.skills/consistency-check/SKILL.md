---
name: consistency-check
description: 一致性检查 - 运行专项一致性检查
argument-hint: "[check_type]"
user-invocable: true
allowed-tools: Read,Bash,Grep
---

# /consistency-check - 一致性检查

## 功能

运行专项一致性检查。

## 使用方式

```
/consistency-check
/consistency-check character
/consistency-check timeline
/consistency-check naming
/consistency-check realm
```

## 检查类型

| 类型 | 说明 |
|------|------|
| character | 人物状态一致性（性别/生死/形态） |
| timeline | 时间线一致性 |
| naming | 命名一致性 |
| realm | 境界体系一致性 |
| faction | 派系关系一致性 |

## 执行流程

1. **解析检查类型**
   - 无参数：运行所有检查
   - 指定类型：只运行指定检查

2. **运行检查脚本**
   ```
   python3 tools/consistency/check_character_state.py
   python3 tools/consistency/check_timeline.py
   ```

3. **输出结果**
   - 发现的问题列表
   - 严重程度
   - 建议修复方案