# 插件系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立标准化插件系统，支持插件接口标准化、插件管理器、安全隔离运行

**Architecture:** 采用插件接口层+插件管理器+沙箱隔离的架构，核心插件在`core_plugins/`目录，用户插件在`plugins/`目录

**Tech Stack:** Python + YAML + importlib + restricted Python

---

## 文件结构

```
novel-factory/
├── plugin_system/
│   ├── __init__.py
│   ├── manager/
│   │   ├── __init__.py
│   │   ├── plugin_manager.py          # 插件管理器
│   │   ├── plugin_registry.py         # 插件注册表
│   │   ├── plugin_loader.py           # 插件加载器
│   │   └── plugin_store.py            # 插件商店
│   ├── interface/
│   │   ├── __init__.py
│   │   ├── base_plugin.py             # 插件基类
│   │   ├── plugin_hook.py            # 钩子定义
│   │   ├── plugin_event.py           # 事件定义
│   │   └── plugin_action.py          # 动作定义
│   ├── sandbox/
│   │   ├── __init__.py
│   │   ├── sandbox.py                # 沙箱环境
│   │   ├── resource_limiter.py       # 资源限制器
│   │   └── api_gateway.py            # API网关
│   ├── core_plugins/
│   │   ├── __init__.py
│   │   ├── narrative_enhancer/        # 叙事增强插件
│   │   │   ├── __init__.py
│   │   │   ├── plugin.yaml
│   │   │   └── main.py
│   │   ├── character_growth/          # 角色成长插件
│   │   ├── editing_revision/          # 编辑修订插件
│   │   ├── scene_enhancer/            # 场景增强插件
│   │   └── world_builder/            # 世界观构建插件
│   └── config/
│       ├── plugin_config.yaml         # 插件配置
│       └── sandbox_config.yaml        # 沙箱配置
└── plugins/                          # 用户安装的插件目录
```

---

### Task 1: 创建插件接口层

**Files:**
- Create: `novel-factory/plugin_system/interface/__init__.py`
- Create: `novel-factory/plugin_system/interface/base_plugin.py`
- Create: `novel-factory/plugin_system/interface/plugin_hook.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_base_plugin.py

import pytest
from plugin_system.interface.base_plugin import (
    BasePlugin,
    PluginMetadata,
    PluginConfig,
    PluginContext
)

def test_plugin_metadata_creation():
    """测试插件元数据创建"""
    metadata = PluginMetadata(
        id="test_plugin",
        name="测试插件",
        version="1.0.0",
        description="一个测试插件",
        author="测试",
        category="testing",
        tags=["test"],
        dependencies=[],
        permissions=["read"]
    )
    assert metadata.id == "test_plugin"
    assert metadata.version == "1.0.0"

def test_plugin_config_defaults():
    """测试插件配置默认值"""
    config = PluginConfig()
    assert config.enabled is True
    assert config.priority == 0

def test_base_plugin_abstract():
    """测试BasePlugin是抽象类"""
    with pytest.raises(TypeError):
        BasePlugin(PluginMetadata(
            id="test",
            name="test",
            version="1.0",
            description="",
            author="",
            category="",
            tags=[],
            dependencies=[],
            permissions=[]
        ))
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory && python -m pytest tests/test_base_plugin.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现插件基类**

```python
# plugin_system/interface/base_plugin.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class PluginMetadata:
    """插件元数据"""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)

@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    priority: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)

class PluginContext:
    """插件上下文"""

    def __init__(self, app_api: 'AppAPI', sandbox: 'Sandbox'):
        self.app_api = app_api
        self.sandbox = sandbox

    def get_content(self, chapter: str) -> str:
        """获取章节内容"""
        return self.app_api.get_chapter_content(chapter)

    def update_content(self, chapter: str, content: str) -> bool:
        """更新章节内容"""
        return self.app_api.update_chapter_content(chapter, content)

    def get_character_profile(self, character_id: str) -> Dict:
        """获取角色特征"""
        return self.app_api.get_character_profile(character_id)

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        self.app_api.log(f"[{self.metadata.name}] {message}", level)

    metadata: Optional[PluginMetadata] = None

class BasePlugin(ABC):
    """插件基类"""

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.config = PluginConfig()
        self._initialized = False
        self._context: Optional[PluginContext] = None

    @abstractmethod
    def initialize(self, context: PluginContext) -> bool:
        """
        初始化插件

        Args:
            context: 插件上下文

        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def execute(self, input_data: Any, context: Dict) -> Any:
        """
        执行插件主逻辑

        Args:
            input_data: 输入数据
            context: 执行上下文

        Returns:
            Any: 执行结果
        """
        pass

    @abstractmethod
    def get_hooks(self) -> List['PluginHook']:
        """
        获取插件注册的钩子

        Returns:
            List[PluginHook]: 钩子列表
        """
        pass

    def shutdown(self) -> None:
        """关闭插件，清理资源"""
        pass

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def update_config(self, config: PluginConfig):
        """更新配置"""
        self.config = config

class AppAPI:
    """应用API（插件可调用的有限接口）"""

    def get_chapter_content(self, chapter: str) -> str:
        """获取章节内容"""
        raise NotImplementedError()

    def update_chapter_content(self, chapter: str, content: str) -> bool:
        """更新章节内容"""
        raise NotImplementedError()

    def get_character_profile(self, character_id: str) -> Dict:
        """获取角色特征"""
        raise NotImplementedError()

    def log(self, message: str, level: str = "info"):
        """记录日志"""
        print(f"[{level.upper()}] {message}")

class Sandbox:
    """沙箱环境"""
    pass
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_base_plugin.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
mkdir -p plugin_system/interface
git add plugin_system/__init__.py plugin_system/interface/__init__.py plugin_system/interface/base_plugin.py
git commit -m "feat(plugin): 添加插件基类"
```

---

### Task 2: 创建钩子定义

**Files:**
- Create: `novel-factory/plugin_system/interface/plugin_hook.py`

- [ ] **Step 1: 创建钩子定义**

```python
# plugin_system/interface/plugin_hook.py

from dataclasses import dataclass
from typing import Any, Callable, List
from enum import Enum

class HookType(Enum):
    """钩子类型"""
    PRE_WRITE = "pre_write"           # 写作前
    POST_WRITE = "post_write"         # 写作后
    PRE_REVIEW = "pre_review"         # 审核前
    POST_REVIEW = "post_review"       # 审核后
    ON_CHARACTER_UPDATE = "on_character_update"  # 角色更新时
    ON_PLOT_EVENT = "on_plot_event"   # 情节事件时

@dataclass
class PluginHook:
    """插件钩子"""
    hook_type: HookType
    callback: Callable
    description: str = ""
    priority: int = 0

class HookManager:
    """钩子管理器"""

    def __init__(self):
        self._hooks: List[PluginHook] = []

    def register_hook(self, hook: PluginHook):
        """注册钩子"""
        self._hooks.append(hook)
        self._hooks.sort(key=lambda h: h.priority, reverse=True)

    def unregister_hook(self, hook_type: HookType, callback: Callable):
        """取消注册钩子"""
        self._hooks = [
            h for h in self._hooks
            if not (h.hook_type == hook_type and h.callback == callback)
        ]

    async def trigger_hook(self, hook_type: HookType, context: dict) -> List[Any]:
        """触发钩子"""
        results = []
        for hook in self._hooks:
            if hook.hook_type == hook_type:
                try:
                    result = await hook.callback(context)
                    results.append(result)
                except Exception as e:
                    # 记录错误但不中断
                    print(f"Hook error: {e}")
        return results

    def get_hooks_by_type(self, hook_type: HookType) -> List[PluginHook]:
        """获取指定类型的钩子"""
        return [h for h in self._hooks if h.hook_type == hook_type]
```

- [ ] **Step 2: 提交**

```bash
git add plugin_system/interface/plugin_hook.py
git commit -m "feat(plugin): 添加钩子定义"
```

---

### Task 3: 实现插件管理器

**Files:**
- Create: `novel-factory/plugin_system/manager/__init__.py`
- Create: `novel-factory/plugin_system/manager/plugin_manager.py`
- Create: `novel-factory/plugin_system/manager/plugin_registry.py`

- [ ] **Step 1: 编写测试**

```python
# tests/test_plugin_manager.py

import pytest
from plugin_system.manager.plugin_manager import PluginManager
from plugin_system.interface.base_plugin import PluginMetadata

def test_plugin_manager_initialization():
    """测试插件管理器初始化"""
    manager = PluginManager()
    assert manager is not None
    assert len(manager.list_plugins()) == 0

def test_register_plugin():
    """测试插件注册"""
    manager = PluginManager()

    class TestPlugin:
        metadata = PluginMetadata(
            id="test",
            name="Test",
            version="1.0",
            description="",
            author="",
            category="",
            tags=[],
            dependencies=[],
            permissions=[]
        )

        def initialize(self, context):
            return True

        def execute(self, input_data, context):
            return input_data

        def get_hooks(self):
            return []

    plugin = TestPlugin()
    result = manager.register_plugin(plugin)
    assert result is True
    assert len(manager.list_plugins()) == 1

def test_enable_disable_plugin():
    """测试启用/禁用插件"""
    manager = PluginManager()

    class TestPlugin:
        metadata = PluginMetadata(
            id="test",
            name="Test",
            version="1.0",
            description="",
            author="",
            category="",
            tags=[],
            dependencies=[],
            permissions=[]
        )

        def initialize(self, context):
            return True

        def execute(self, input_data, context):
            return input_data

        def get_hooks(self):
            return []

    plugin = TestPlugin()
    manager.register_plugin(plugin)

    assert manager.is_enabled("test") is True

    manager.disable_plugin("test")
    assert manager.is_enabled("test") is False

    manager.enable_plugin("test")
    assert manager.is_enabled("test") is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_plugin_manager.py -v`
Expected: FAIL with "cannot import"

- [ ] **Step 3: 实现插件注册表**

```python
# plugin_system/manager/plugin_registry.py

from typing import Dict, List, Optional
from dataclasses import dataclass
from plugin_system.interface.base_plugin import PluginMetadata

@dataclass
class PluginRecord:
    """插件记录"""
    metadata: PluginMetadata
    enabled: bool = True
    loaded: bool = False
    instance: Optional[object] = None
    error: Optional[str] = None

class PluginRegistry:
    """插件注册表"""

    def __init__(self):
        self._plugins: Dict[str, PluginRecord] = {}

    def register(self, metadata: PluginMetadata) -> bool:
        """注册插件"""
        if metadata.id in self._plugins:
            return False

        self._plugins[metadata.id] = PluginRecord(metadata=metadata)
        return True

    def unregister(self, plugin_id: str) -> bool:
        """取消注册"""
        if plugin_id not in self._plugins:
            return False

        del self._plugins[plugin_id]
        return True

    def get(self, plugin_id: str) -> Optional[PluginRecord]:
        """获取插件记录"""
        return self._plugins.get(plugin_id)

    def list_all(self) -> List[PluginRecord]:
        """列出所有插件"""
        return list(self._plugins.values())

    def list_enabled(self) -> List[PluginRecord]:
        """列出启用的插件"""
        return [p for p in self._plugins.values() if p.enabled]

    def list_by_category(self, category: str) -> List[PluginRecord]:
        """按类别列出插件"""
        return [
            p for p in self._plugins.values()
            if p.metadata.category == category
        ]
```

- [ ] **Step 4: 实现插件管理器**

```python
# plugin_system/manager/plugin_manager.py

from typing import Dict, List, Any, Optional
import importlib
import yaml
from pathlib import Path

from plugin_system.interface.base_plugin import (
    BasePlugin,
    PluginMetadata,
    PluginContext,
    AppAPI
)
from plugin_system.interface.plugin_hook import HookManager
from .plugin_registry import PluginRegistry, PluginRecord

class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.registry = PluginRegistry()
        self.hook_manager = HookManager()
        self._app_api: Optional[AppAPI] = None

    def set_app_api(self, app_api: AppAPI):
        """设置应用API"""
        self._app_api = app_api

    def register_plugin(self, plugin: BasePlugin) -> bool:
        """注册插件"""
        if not isinstance(plugin, BasePlugin):
            return False

        metadata = plugin.metadata
        if not self.registry.register(metadata):
            return False

        # 获取记录并设置实例
        record = self.registry.get(metadata.id)
        if record:
            record.instance = plugin
            record.loaded = True

        # 注册钩子
        for hook in plugin.get_hooks():
            self.hook_manager.register_hook(hook)

        return True

    def unregister_plugin(self, plugin_id: str) -> bool:
        """取消注册插件"""
        record = self.registry.get(plugin_id)
        if not record or not record.instance:
            return False

        # 取消注册钩子
        plugin = record.instance
        for hook in plugin.get_hooks():
            self.hook_manager.unregister_hook(hook.hook_type, hook.callback)

        # 关闭插件
        plugin.shutdown()

        return self.registry.unregister(plugin_id)

    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        record = self.registry.get(plugin_id)
        if not record:
            return False
        record.enabled = True
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        record = self.registry.get(plugin_id)
        if not record:
            return False
        record.enabled = False
        return True

    def is_enabled(self, plugin_id: str) -> bool:
        """检查插件是否启用"""
        record = self.registry.get(plugin_id)
        return record.enabled if record else False

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        result = []
        for record in self.registry.list_all():
            result.append({
                'id': record.metadata.id,
                'name': record.metadata.name,
                'version': record.metadata.version,
                'category': record.metadata.category,
                'enabled': record.enabled,
                'loaded': record.loaded,
                'error': record.error
            })
        return result

    async def execute_plugin(
        self,
        plugin_id: str,
        input_data: Any,
        context: Dict
    ) -> Any:
        """执行插件"""
        record = self.registry.get(plugin_id)
        if not record or not record.instance:
            raise ValueError(f"Plugin {plugin_id} not found")

        if not record.enabled:
            raise ValueError(f"Plugin {plugin_id} is disabled")

        plugin = record.instance

        # 确保插件已初始化
        if not plugin.is_initialized:
            plugin_context = PluginContext(self._app_api, None)
            plugin.metadata = record.metadata
            if not await plugin.initialize(plugin_context):
                raise RuntimeError(f"Plugin {plugin_id} initialization failed")

        return await plugin.execute(input_data, context)

    def load_plugin_from_file(self, plugin_path: Path) -> bool:
        """从文件加载插件"""
        try:
            # 读取插件配置
            config_path = plugin_path / "plugin.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 动态导入模块
            main_file = plugin_path / "main.py"
            if not main_file.exists():
                return False

            spec = importlib.util.spec_from_file_location(
                "plugin_module",
                main_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 查找插件类
            plugin_class = getattr(module, config['main_class'], None)
            if not plugin_class:
                return False

            # 创建实例
            metadata = PluginMetadata(**config['metadata'])
            plugin_instance = plugin_class(metadata)

            return self.register_plugin(plugin_instance)

        except Exception as e:
            print(f"Failed to load plugin from {plugin_path}: {e}")
            return False

    def discover_plugins(self) -> int:
        """发现并加载插件目录下的所有插件"""
        count = 0
        if not self.plugin_dir.exists():
            return 0

        for item in self.plugin_dir.iterdir():
            if item.is_dir() and (item / "plugin.yaml").exists():
                if self.load_plugin_from_file(item):
                    count += 1

        return count
```

- [ ] **Step 5: 运行测试验证通过**

Run: `python -m pytest tests/test_plugin_manager.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
mkdir -p plugin_system/manager
git add plugin_system/manager/__init__.py plugin_system/manager/plugin_registry.py plugin_system/manager/plugin_manager.py
git commit -m "feat(plugin): 实现插件管理器和注册表"
```

---

### Task 4: 创建叙事增强核心插件

**Files:**
- Create: `novel-factory/plugin_system/core_plugins/narrative_enhancer/__init__.py`
- Create: `novel-factory/plugin_system/core_plugins/narrative_enhancer/plugin.yaml`
- Create: `novel-factory/plugin_system/core_plugins/narrative_enhancer/main.py`

- [ ] **Step 1: 创建叙事增强插件配置**

```yaml
# plugin_system/core_plugins/narrative_enhancer/plugin.yaml

metadata:
  id: narrative_enhancer
  name: 叙事增强
  version: 1.0.0
  description: 增强叙事连贯性和情感表达
  author: novel_factory
  category: narrative
  tags:
    - narrative
    - coherence
    - emotion
  dependencies: []
  permissions:
    - read
    - write

main_class: NarrativeEnhancerPlugin

settings:
  enabled: true
  enhance_dialogue: true
  enhance_description: true
  add_transitions: true
```

- [ ] **Step 2: 创建叙事增强插件主逻辑**

```python
# plugin_system/core_plugins/narrative_enhancer/main.py

from typing import Any, Dict, List
from plugin_system.interface.base_plugin import (
    BasePlugin,
    PluginMetadata,
    PluginContext
)
from plugin_system.interface.plugin_hook import PluginHook, HookType

class NarrativeEnhancerPlugin(BasePlugin):
    """叙事增强插件"""

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self._context: PluginContext = None

    def initialize(self, context: PluginContext) -> bool:
        """初始化插件"""
        self._context = context
        self._context.metadata = self.metadata
        self._initialized = True
        return True

    def execute(self, input_data: Any, context: Dict) -> Any:
        """执行叙事增强"""
        if not isinstance(input_data, str):
            return input_data

        text = input_data
        results = []

        # 增强对话
        if self.config.settings.get('enhance_dialogue', True):
            enhanced = self._enhance_dialogue(text)
            results.append(('dialogue', enhanced))

        # 增强描写
        if self.config.settings.get('enhance_description', True):
            enhanced = self._enhance_description(text)
            results.append(('description', enhanced))

        # 添加过渡
        if self.config.settings.get('add_transitions', True):
            enhanced = self._add_transitions(text)
            results.append(('transitions', enhanced))

        return {
            'original': text,
            'enhancements': dict(results),
            'plugin': self.metadata.name
        }

    def _enhance_dialogue(self, text: str) -> str:
        """增强对话"""
        # 简化：添加更多对话标签变化
        import re

        # 找到对话
        pattern = r'[""]([^""]+)[""]'
        dialogues = re.findall(pattern, text)

        if not dialogues:
            return text

        # 简单增强：将部分"说"替换为更丰富的标签
        enhanced = text
        for dialogue in dialogues[:3]:  # 最多处理3处
            if f'说："{dialogue}"' in enhanced:
                enhanced = enhanced.replace(
                    f'说："{dialogue}"',
                    f'轻声道："{dialogue}"',
                    1
                )

        return enhanced

    def _enhance_description(self, text: str) -> str:
        """增强描写"""
        # 简化：添加感官词汇
        keywords = ['看', '听', '感觉']

        for kw in keywords:
            if kw in text and f'轻轻地{kw}' not in text:
                text = text.replace(f'{kw}到', f'轻轻地{kw}到')

        return text

    def _add_transitions(self, text: str) -> str:
        """添加过渡"""
        # 简化：在段落间添加过渡词
        paragraphs = text.split('\n\n')
        if len(paragraphs) < 2:
            return text

        enhanced_paragraphs = [paragraphs[0]]
        transitions = ['随后', '紧接着', '与此同时', '不久之后']

        for i, para in enumerate(paragraphs[1:], 1):
            if para.strip():
                transition = transitions[i % len(transitions)]
                enhanced_paragraphs.append(f'{transition}，{para}')

        return '\n\n'.join(enhanced_paragraphs)

    def get_hooks(self) -> List[PluginHook]:
        """获取钩子"""
        return [
            PluginHook(
                hook_type=HookType.POST_WRITE,
                callback=self._on_post_write,
                description="增强叙事",
                priority=10
            )
        ]

    async def _on_post_write(self, context: dict) -> dict:
        """写作后钩子回调"""
        content = context.get('content', '')
        if content:
            result = self.execute(content, context)
            context['enhanced_content'] = result.get('enhancements', {})
        return context
```

- [ ] **Step 3: 提交核心插件**

```bash
mkdir -p plugin_system/core_plugins/narrative_enhancer
git add plugin_system/core_plugins/__init__.py plugin_system/core_plugins/narrative_enhancer/__init__.py
git add plugin_system/core_plugins/narrative_enhancer/plugin.yaml plugin_system/core_plugins/narrative_enhancer/main.py
git commit -m "feat(plugin): 添加叙事增强核心插件"
```

---

### Task 5: 创建配置文件

**Files:**
- Create: `novel-factory/plugin_system/config/plugin_config.yaml`
- Create: `novel-factory/plugin_system/config/sandbox_config.yaml`

- [ ] **Step 1: 创建配置文件**

```yaml
# plugin_system/config/plugin_config.yaml

# 插件系统配置
# 最后更新：2026-05-19

# 插件目录
plugin_directories:
  - plugins/                 # 用户插件
  - plugin_system/core_plugins/  # 核心插件

# 启用/禁用核心插件
core_plugins:
  narrative_enhancer:
    enabled: true
    priority: 10
  character_growth:
    enabled: false
  editing_revision:
    enabled: false
  scene_enhancer:
    enabled: false
  world_builder:
    enabled: false

# 自动加载
auto_load: true
auto_load_on_startup: true

# 日志
logging:
  level: info
  log_plugin_hooks: false
```

```yaml
# plugin_system/config/sandbox_config.yaml

# 沙箱配置
# 最后更新：2026-05-19

# 资源限制
resource_limits:
  max_memory_mb: 256
  max_cpu_percent: 50
  max_execution_time_seconds: 30

# API限制
api_restrictions:
  allowed_apis:
    - get_chapter_content
    - get_character_profile
    - log
    - get_pacing_data

  denied_apis:
    - delete_file
    - network_request
    - execute_code

# 导入限制
import_restrictions:
  allowed_modules:
    - typing
    - re
    - datetime
    - json

  denied_modules:
    - os
    - sys
    - subprocess
    - socket
```

- [ ] **Step 2: 提交配置文件**

```bash
mkdir -p plugin_system/config
git add plugin_system/config/plugin_config.yaml plugin_system/config/sandbox_config.yaml
git commit -m "feat(plugin): 添加插件系统配置文件"
```

---

## 实现完成检查

- [ ] 插件接口层已创建
- [ ] 插件基类已实现
- [ ] 钩子定义已创建
- [ ] 插件管理器已实现
- [ ] 插件注册表已实现
- [ ] 叙事增强核心插件已创建
- [ ] 配置文件已创建
- [ ] 测试通过