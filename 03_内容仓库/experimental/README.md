# 工程验证正文（非产品交付）

本目录说明 **不属于正史交付范围** 的正文产物。

## stress-test-ch361-996

| 项 | 值 |
|----|-----|
| 范围 | `04_正文/ch361.md` … `ch996.md`（636 章） |
| 性质 | canon epilogue **压力测试** / 流水线验收集 |
| 正史终点 | **ch360**（见 `config/project.yaml` → `max_chapter: 360`） |
| 大纲 | 无 ch361+ 分章大纲 |
| 审核 | 未走 S1–S8 人审流程 |

**不要**将这些章节当作《星陨纪元》续作或发布内容。  
保留用途：RAG 负载基准、batch 稳定性回归、负例（无大纲续写）。

生产硬门（Phase 10.01）默认禁止 ch361+ canon 落盘；  
仅当显式设置 `LINGWEN_ALLOW_STRESS_TEST=1` 时可续跑 stress test。
