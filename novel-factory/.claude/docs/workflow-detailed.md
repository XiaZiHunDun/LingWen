# 工作流详细步骤

## 25 步闭环工作流

### PHASE_1_LAUNCH (立项)
- STEP_01 → STEP_02

### PHASE_2_OUTLINE (全文大纲迭代)
- STEP_03 → STEP_04 → STEP_05

### PHASE_3_VOLUME (卷大纲迭代)
- STEP_06 → STEP_07 → STEP_08 → STEP_09

### PHASE_4_STAGE (阶段大纲迭代)
- STEP_10 → STEP_11 → STEP_12 → STEP_13

### PHASE_5_BODY (正文创作与双轨反馈)
- STEP_14 → STEP_15 → STEP_16 → STEP_17 → STEP_18

### PHASE_6_SUMMARY (分层汇总与终审)
- STEP_19 → STEP_20 → STEP_21 → STEP_22 → STEP_23 → STEP_24

### PHASE_7_CLOSE (归档闭环)
- STEP_25

---

## 状态机文件结构

`workflow_state.json` 结构：

```json
{
  "version": "v3.0",
  "current_phase": "PHASE_X_Y",
  "current_step": "STEP_XX",
  "phases": {
    "PHASE_X_Y": {
      "steps": {
        "STEP_XX": {
          "status": "completed|in_progress|pending",
          "output": [...],
          "verdict": "通过|不通过|需修改"
        }
      }
    }
  },
  "agent_tasks": {...}
}
```
