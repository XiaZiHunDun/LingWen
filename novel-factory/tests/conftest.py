"""pytest 配置"""
import os
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 确保项目根目录在 sys.path 中（支持 pythonpath = . 配置）
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest


@pytest.fixture(autouse=True)
def _restore_lingwen_project_root():
    """activate_project() sets os.environ directly; restore after each test."""
    from infra.paths import ProjectPaths

    saved = os.environ.get("LINGWEN_PROJECT_ROOT")
    yield
    if saved is None:
        os.environ.pop("LINGWEN_PROJECT_ROOT", None)
    else:
        os.environ["LINGWEN_PROJECT_ROOT"] = saved
    ProjectPaths.reset()


@pytest.fixture
def project_root():
    """项目根目录 fixture"""
    return PROJECT_ROOT


@pytest.fixture
def chapters_dir():
    """章节目录 fixture"""
    return PROJECT_ROOT / "03_内容仓库" / "04_正文"


@pytest.fixture
def sample_chapter():
    """示例章节 fixture"""
    return """# 第1章 新的开始

这是一个测试章节的内容。
星月看着眼前的景象，心中充满了期待。

**本章完**
"""
