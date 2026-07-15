# 小说工厂 v9.x 问题修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复小说工厂所有P0/P1/P2级问题，提升系统稳定性、可用性和性能

**Architecture:** 分三个阶段修复：P0紧急问题 → P1重要改进 → P2性能优化。每个阶段独立可测试。

**Tech Stack:** Python 3.13, pytest, SQLite, 正则表达式

---

## 阶段一：P0紧急问题修复

### Task 1.1: 修复 test_rejection_transition 测试失败

**Files:**
- Modify: `novel-factory/infra/state/workflow_validator.py:36`
- Modify: `novel-factory/tests/test_workflow_validator.py:29-34`

**Analysis:** workflow_validator.py:36 定义 `STEP_18: ['STEP_18a', 'STEP_19']`，不含 STEP_16。但自测代码第129行包含 `('STEP_18', 'STEP_16')` 作为"合法转换"。测试假设 STEP_18 可退回到 STEP_16，但实现不支持。

**Decision:** 业务上需要确认：STEP_18 验证失败后是否允许退回到 STEP_16 重新修改？根据工作流逻辑，STEP_18 是"章节定稿判定"，如果判定失败应该允许退回到 STEP_16（审核期）重新修改。因此应该修改 VALID_TRANSITIONS 支持这个转换。

- [ ] **Step 1: 确认业务规则并修改 VALID_TRANSITIONS**

```python
# novel-factory/infra/state/workflow_validator.py:36
# 修改前:
'STEP_18': ['STEP_18a', 'STEP_19'],  # 验证失败可退回重写或进入LLM质检

# 修改后:
'STEP_18': ['STEP_18a', 'STEP_19', 'STEP_16'],  # 验证失败可退回审核重写或进入LLM质检
```

Run: `grep -n "STEP_18.*STEP_18a" novel-factory/infra/state/workflow_validator.py`
Expected: 显示修改后的行

- [ ] **Step 2: 运行测试验证修复**

Run: `cd novel-factory && python -m pytest tests/test_workflow_validator.py::TestValidateTransition::test_rejection_transition -v`
Expected: PASS

- [ ] **Step 3: 运行完整 validator 测试**

Run: `cd novel-factory && python -m pytest tests/test_workflow_validator.py -v`
Expected: 全部 PASS (699 passed, 2 skipped)

- [ ] **Step 4: 提交**

```bash
git add novel-factory/infra/state/workflow_validator.py
git commit -m "fix: add STEP_16 to allowed transitions from STEP_18"
```

---

### Task 1.2: 恢复空章节文件 ch009.md 和 ch015.md

**Files:**
- Create: `novel-factory/03_内容仓库/04_正文/ch009.md`
- Create: `novel-factory/03_内容仓库/04_正文/ch015.md`

**Analysis:** 这两个文件大小为 0 字节，内容完全缺失。需要从 Git 历史恢复或基于前后章节上下文重新生成。

**Decision:** 从 Git 历史恢复是最可靠的方式，因为这是已发布的内容，不应该重新生成。

- [ ] **Step 1: 从 Git 历史恢复 ch009.md**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen && git show HEAD~5:novel-factory/03_内容仓库/04_正文/ch009.md > novel-factory/03_内容仓库/04_正文/ch009.md 2>&1 || echo "checking alternate commit"`
Expected: 文件大小 > 0

- [ ] **Step 2: 检查 Git 中的 ch009 历史版本**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen && git log --oneline -- novel-factory/03_内容仓库/04_正文/ch009.md | head -5`
Expected: 显示提交历史

- [ ] **Step 3: 从历史版本恢复**

如果历史存在:
```bash
git checkout <commit-hash> -- novel-factory/03_内容仓库/04_正文/ch009.md
git checkout <commit-hash> -- novel-factory/03_内容仓库/04_正文/ch015.md
```

如果历史不存在（文件从未提交过）:
```bash
# 基于 ch008.md 和 ch010.md 的上下文生成临时内容
# 注意：这需要人工审核确认
```

- [ ] **Step 4: 验证文件恢复成功**

Run: `wc -l novel-factory/03_内容仓库/04_正文/ch009.md novel-factory/03_内容仓库/04_正文/ch015.md`
Expected: 两个文件都有内容（行数 > 0）

- [ ] **Step 5: 提交**

```bash
git add novel-factory/03_内容仓库/04_正文/ch009.md novel-factory/03_内容仓库/04_正文/ch015.md
git commit -m "fix: restore empty chapter files ch009 and ch015"
```

---

### Task 1.3: 统一状态管理系统（消除双轨混乱）

**Files:**
- Modify: `novel-factory/infra/agent_system/task_orchestrator.py:34`
- Modify: `novel-factory/infra/agent_system/master_controller.py:68-70`
- Deprecate: `novel-factory/workflow_state.json` (标记为 deprecated，不删除保留备份)

**Analysis:** MasterController 和 TaskOrchestrator 仍使用 workflow_state.json，但 StateManager 已迁移到 SQLite。两套系统并存造成状态不一致。

**Decision:** TaskOrchestrator 接受 state_manager 实例而非 state_file 路径。MasterController 创建 StateManager 实例并传入 TaskOrchestrator。workflow_state.json 保留但标记为 deprecated。

- [ ] **Step 1: 修改 TaskOrchestrator 初始化逻辑**

```python
# novel-factory/infra/agent_system/task_orchestrator.py:30-49
# 修改前:
def __init__(
    self,
    state_manager: Optional[Any] = None,
    event_bus: Optional[EventBus] = None,
    state_file: str = "workflow_state.json"
):
    self._state_file = state_file
    self._event_bus = event_bus or EventBus()
    if state_manager is None:
        from infra.state.state_manager import StateManager
        state_manager = StateManager()

# 修改后:
def __init__(
    self,
    state_manager: Optional[Any] = None,
    event_bus: Optional[EventBus] = None
):
    self._event_bus = event_bus or EventBus()
    if state_manager is None:
        from infra.state.state_manager import StateManager
        state_manager = StateManager()
    self._state_manager = state_manager
```

- [ ] **Step 2: 修改 MasterController 创建 TaskOrchestrator 的方式**

```python
# novel-factory/infra/agent_system/master_controller.py:67-70
# 修改前:
self._orchestrator = TaskOrchestrator(
    state_file=f"{state_dir}/workflow_state.json"
)

# 修改后:
from infra.state.state_manager import StateManager
self._orchestrator = TaskOrchestrator(
    state_manager=StateManager()
)
```

- [ ] **Step 3: 添加 workflow_state.json 废弃标记**

在 `novel-factory/workflow_state.json` 顶部添加:
```json
{
  "_deprecated": "此文件已被 .state/workflow.db 替代，请勿修改",
  "version": "v9.1-deprecated",
  ...
}
```

- [ ] **Step 4: 更新 CLAUDE.md 文档**

将 CLAUDE.md 中 "workflow_state.json - 状态机文件" 改为 "SQLite - .state/workflow.db"

- [ ] **Step 5: 运行测试验证**

Run: `cd novel-factory && python -m pytest tests/test_workflow_validator.py tests/test_workflow_state.py -v`
Expected: 全部 PASS

- [ ] **Step 6: 提交**

```bash
git add novel-factory/infra/agent_system/task_orchestrator.py novel-factory/infra/agent_system/master_controller.py novel-factory/workflow_state.json novel-factory/CLAUDE.md
git commit -m "refactor: unify state management to SQLite, deprecate workflow_state.json"
```

---

## 阶段二：P1重要问题改进

### Task 2.1: 修复裸异常捕获问题

**Files:**
- Modify: `novel-factory/infra/memory_service.py:133,171,204,255`

**Analysis:** 多处使用 `except Exception as e` 静默吞掉异常，仅记录 warning 后使用降级配置继续执行。正确的做法是区分异常类型：配置缺失使用 warning，编程错误使用 error。

**Decision:** 改为具体异常类型 + logging.error(exc_info=True) 记录完整堆栈。

- [ ] **Step 1: 修改 memory_service.py 第133行**

```python
# novel-factory/infra/memory_service.py:130-155
# 修改前:
try:
    config = load_yaml("config/memory_config.yaml")
    return config
except Exception as e:
    logger.warning(f"无法加载 memory_config.yaml，使用内联默认配置: {e}")
    return {...}

# 修改后:
try:
    config = load_yaml("config/memory_config.yaml")
    return config
except FileNotFoundError as e:
    logger.warning(f"memory_config.yaml 未找到，使用内联默认配置: {e}")
    return {...}
except (yaml.YAMLError, OSError) as e:
    logger.error(f"加载 memory_config.yaml 失败: {e}", exc_info=True)
    return {...}
```

- [ ] **Step 2: 修改 memory_service.py 第171行**

```python
# 修改前:
except Exception as e:
    logger.warning(f"Qdrant 连接检查失败: {e}")
    return False

# 修改后:
except (ConnectionError, TimeoutError, OSError) as e:
    logger.warning(f"Qdrant 连接检查失败: {e}")
    return False
except Exception as e:
    logger.error(f"Qdrant 连接检查时发生未预期错误: {e}", exc_info=True)
    return False
```

- [ ] **Step 3: 修改 memory_service.py 第204行和第255行**

Run: `grep -n "except Exception" novel-factory/infra/memory_service.py`
Expected: 显示所有 except Exception 位置

使用相同模式修改剩余位置，区分 FileNotFoundError/OSError 与其他异常。

- [ ] **Step 4: 运行测试验证**

Run: `cd novel-factory && python -m pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/memory_service.py
git commit -m "fix: improve exception handling with specific types and proper logging"
```

---

### Task 2.2: 生成缺失的37章章节大纲

**Files:**
- Execute: `novel-factory/tools/generate_chapter_outlines.py`

**Analysis:** 37个章节大纲文件缺失（ch009, ch015, ch027, ch045, ch047, ch075, ch079, ch088, ch101, ch104, ch105, ch107, ch110, ch112, ch114, ch126, ch133, ch194, ch195, ch196, ch201, ch203, ch238, ch243, ch250, ch268, ch271, ch291, ch294, ch300, ch302, ch316, ch344, ch345, ch351, ch353, ch357）

**Decision:** 使用现有的 generate_chapter_outlines.py 工具批量生成缺失的大纲文件。

- [ ] **Step 1: 检查工具是否可用**

Run: `cd novel-factory && python tools/generate_chapter_outlines.py --help`
Expected: 显示帮助信息

- [ ] **Step 2: 识别缺失的大纲文件**

Run: `ls novel-factory/03_内容仓库/04_正文/ch*_大纲.md | wc -l && ls novel-factory/03_内容仓库/04_正文/ch*_大纲.md | grep -E "ch009|ch015|ch027|ch045|ch047" | head -5`
Expected: 显示缺失的大纲文件

- [ ] **Step 3: 生成缺失的大纲**

```bash
cd novel-factory
python tools/generate_chapter_outlines.py --chapters 9,15,27,45,47,75,79,88,101,104,105,107,110,112,114,126,133,194,195,196,201,203,238,243,250,268,271,291,294,300,302,316,344,345,351,353,357
```

- [ ] **Step 4: 验证生成结果**

Run: `ls novel-factory/03_内容仓库/04_正文/ch*_大纲.md | wc -l`
Expected: 360 (完整的大纲文件)

- [ ] **Step 5: 提交**

```bash
git add novel-factory/03_内容仓库/04_正文/ch*_大纲.md
git commit -m "feat: generate missing chapter outlines for 37 chapters"
```

---

### Task 2.3: 整理归档文档

**Files:**
- Archive: `novel-factory/docs/优化方案-v8.0.md` → `novel-factory/docs/archive/优化方案-v8.0.md`
- Archive: `novel-factory/docs/优化方案-v8.1.md` → `novel-factory/docs/archive/优化方案-v8.1.md`
- Modify: `novel-factory/docs/优化方案-v9.1.md` (添加状态和日期)
- Modify: `novel-factory/docs/运转流程.md` (确保版本与 workflow_state.json 一致)

**Analysis:** 存在多个版本的优化方案文档，新人无法判断哪个是最新。旧版本应移至 archive 目录。

**Decision:** 创建 docs/archive/ 目录，将旧版本移入。最新文档添加版本和状态标记。

- [ ] **Step 1: 创建 archive 目录**

Run: `mkdir -p novel-factory/docs/archive`
Expected: 目录创建成功

- [ ] **Step 2: 移动旧版本文档**

```bash
mv novel-factory/docs/优化方案-v8.0.md novel-factory/docs/archive/
mv novel-factory/docs/优化方案-v8.1.md novel-factory/docs/archive/
```

- [ ] **Step 3: 更新优化方案-v9.1.md 状态**

在文件顶部添加状态标记:
```markdown
> **文档版本**: v9.1
> **创建时间**: 2026-05-20
> **更新时间**: 2026-05-24
> **状态**: 已归档 (v9.2 发布后归档)
```

- [ ] **Step 4: 更新运转流程.md 版本**

确认文档顶部版本为 v9.1 (与 workflow_state.json 一致)

- [ ] **Step 5: 创建 README.md 索引**

```markdown
# novel-factory 文档索引

## 当前使用文档
- `运转流程.md` - 小说工厂运转指南 (v9.1)
- `优化方案-v9.1.md` - 已归档

## 历史版本 (archive/)
- `优化方案-v8.0.md` - v8.0 优化方案
- `优化方案-v8.1.md` - v8.1 优化方案
```

- [ ] **Step 6: 提交**

```bash
git add novel-factory/docs/archive/ novel-factory/docs/优化方案-v9.1.md novel-factory/docs/运转流程.md novel-factory/docs/README.md
git commit -m "docs: archive old optimization docs and add index"
```

---

## 阶段三：P2性能优化

### Task 3.1: 并行化 LLM 检测调用

**Files:**
- Modify: `novel-factory/tools/llm_quality_deep_check.py:416-461`

**Analysis:** STEP_18b/18c/18d 使用串行 for 循环，只有 STEP_18a 使用并行。4个检测步骤可以合并为1次 LLM 调用返回多维度结果。

**Decision:** 短期：将 STEP_18b/18c/18d 也改为并行执行。长期：合并为单次多维度调用。

- [ ] **Step 1: 分析当前串行实现**

Run: `sed -n '416,461p' novel-factory/tools/llm_quality_deep_check.py`
Expected: 显示 run_phase_18b/c/d 的串行代码

- [ ] **Step 2: 修改 run_phase_18b 为并行**

```python
# novel-factory/tools/llm_quality_deep_check.py
# 修改前 (第421-428行):
for ch in chapters:
    content = checker.load_chapter(ch)
    if content:
        context_chs = [c for c in range(ch - 5, ch + 6) if c != ch and 1 <= c <= 360]
        report = checker.scan_logic_contradictions(ch, content, context_chs)
        reports[ch] = report

# 修改后:
if parallel:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for ch in chapters:
            content = checker.load_chapter(ch)
            if content:
                context_chs = [c for c in range(ch - 5, ch + 6) if c != ch and 1 <= c <= 360]
                future = executor.submit(checker.scan_logic_contradictions, ch, content, context_chs)
                futures[future] = ch
        for future in as_completed(futures):
            ch = futures[future]
            try:
                reports[ch] = future.result()
            except Exception as e:
                print(f"  ch{ch:03d}: 错误 - {e}")
else:
    for ch in chapters:
        content = checker.load_chapter(ch)
        if content:
            context_chs = [c for c in range(ch - 5, ch + 6) if c != ch and 1 <= c <= 360]
            report = checker.scan_logic_contradictions(ch, content, context_chs)
            reports[ch] = report
```

- [ ] **Step 3: 同样修改 run_phase_18c 和 run_phase_18d**

使用相同的并行化模式修改 run_phase_18c (第438-443行) 和 run_phase_18d (第453-458行)

- [ ] **Step 4: 测试并行化效果**

Run: `cd novel-factory && python tools/llm_quality_deep_check.py --check logic --chapters 1-30 --parallel 2>&1 | head -30`
Expected: 显示并行执行日志

- [ ] **Step 5: 提交**

```bash
git add novel-factory/tools/llm_quality_deep_check.py
git commit -m "perf: parallelize STEP_18b/c/d LLM detection calls"
```

---

### Task 3.2: 优化检测器性能（句式多样性检测器）

**Files:**
- Modify: `novel-factory/infra/consistency/checkers/sentence_diversity_checker.py`

**Analysis:** SentenceDiversityChecker 使用 145+ 正则模式全量遍历，每章耗时 200-500ms。可以使用预编译正则和置信度阈值优化。

**Decision:** 预编译正则表达式，避免每次匹配时重新编译。

- [ ] **Step 1: 分析当前实现**

Run: `head -60 novel-factory/infra/consistency/checkers/sentence_diversity_checker.py`
Expected: 显示 DIVERSE_PATTERNS 定义位置

- [ ] **Step 2: 添加正则预编译**

```python
# novel-factory/infra/consistency/checkers/sentence_diversity_checker.py
# 在 DIVERSE_PATTERNS 定义后添加:
_COMPILED_PATTERNS = None

def _get_compiled_patterns():
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is None:
        _COMPILED_PATTERNS = [(re.compile(pattern), name, label) for pattern, name, label in DIVERSE_PATTERNS]
    return _COMPILED_PATTERNS
```

- [ ] **Step 3: 修改 check 方法使用预编译正则**

找到使用 DIVERSE_PATTERNS 的代码，改为使用 _get_compiled_patterns()

- [ ] **Step 4: 运行测试验证**

Run: `cd novel-factory && python -m pytest tests/ -k "sentence" -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add novel-factory/infra/consistency/checkers/sentence_diversity_checker.py
git commit -m "perf: pre-compile regex patterns in SentenceDiversityChecker"
```

---

### Task 3.3: 外部化硬编码模式库到 YAML

**Files:**
- Create: `novel-factory/tools/rules/sentence_diversity_rules.yaml`
- Create: `novel-factory/tools/rules/template_sentence_rules.yaml`
- Modify: `novel-factory/infra/consistency/checkers/sentence_diversity_checker.py`

**Analysis:** 170+ 行硬编码模式在代码中，难以维护和动态更新。应迁移到 YAML 配置文件。

**Decision:** 创建 YAML 配置文件，加载时读取，避免每次修改源码。

- [ ] **Step 1: 创建 sentence_diversity_rules.yaml**

```yaml
# novel-factory/tools/rules/sentence_diversity_rules.yaml
diverse_patterns:
  - pattern: '「[^」]+」'
    name: 'dialog'
    label: '对话句'
  - pattern: '"[^"]+"'
    name: 'dialog_english'
    label: '对话句(英文)'
  # ... 其他模式

template_patterns:
  - pattern: '他[说问道喊叫笑叹谓称著显示露出透露出冒][^。！？]{0,15}[。！？]'
    name: '模板_他说道'
    suggestions:
      - '减少"他说道"的使用，用动作和表情替代'
      - '改为：他抬起下巴，目光冷冽'
```

- [ ] **Step 2: 修改 SentenceDiversityChecker 加载 YAML**

```python
# novel-factory/infra/consistency/checkers/sentence_diversity_checker.py
import yaml
from pathlib import Path

def _load_patterns_from_yaml():
    rules_dir = Path(__file__).parent.parent.parent.parent / 'tools' / 'rules'
    diverse_path = rules_dir / 'sentence_diversity_rules.yaml'
    template_path = rules_dir / 'template_sentence_rules.yaml'
    
    patterns = {'diverse': [], 'template': []}
    if diverse_path.exists():
        with open(diverse_path) as f:
            data = yaml.safe_load(f)
            patterns['diverse'] = [(p['pattern'], p['name'], p['label']) for p in data.get('diverse_patterns', [])]
    if template_path.exists():
        with open(template_path) as f:
            data = yaml.safe_load(f)
            patterns['template'] = [(p['pattern'], p['name'], p.get('suggestions', [])) for p in data.get('template_patterns', [])]
    return patterns
```

- [ ] **Step 3: 添加 fallback 到硬编码模式**

```python
def _get_patterns():
    patterns = _load_patterns_from_yaml()
    if not patterns['diverse']:
        return DIVERSE_PATTERNS, TEMPLATE_PATTERNS
    return patterns['diverse'], patterns['template']
```

- [ ] **Step 4: 运行测试验证**

Run: `cd novel-factory && python -m pytest tests/ -k "sentence" -v`
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add novel-factory/tools/rules/sentence_diversity_rules.yaml novel-factory/tools/rules/template_sentence_rules.yaml novel-factory/infra/consistency/checkers/sentence_diversity_checker.py
git commit -m "refactor: externalize pattern definitions to YAML config"
```

---

## 执行摘要

| Task | 预估时间 | 依赖 |
|------|----------|------|
| 1.1 test_rejection_transition | 10分钟 | 无 |
| 1.2 恢复空章节文件 | 30分钟 | 无 |
| 1.3 统一状态管理 | 2小时 | 1.1 |
| 2.1 修复裸异常捕获 | 3小时 | 无 |
| 2.2 生成缺失大纲 | 1小时 | 无 |
| 2.3 整理归档文档 | 1小时 | 无 |
| 3.1 并行化LLM调用 | 4小时 | 1.3 |
| 3.2 优化检测器性能 | 3小时 | 无 |
| 3.3 外部化模式库 | 4小时 | 无 |

**总计预估**: ~18小时

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-24-novel-factory-fix-plan.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?