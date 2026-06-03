import shutil
import tempfile
from pathlib import Path

from infra.cache import CheckerCache


def test_cache_set_and_get():
    cache_dir = tempfile.mkdtemp()
    try:
        cache = CheckerCache(cache_dir=cache_dir)
        result = {"issues": [], "score": 0.9}
        cache.set("test_checker", 1, "测试内容", result)
        cached = cache.get("test_checker", 1, "测试内容")
        assert cached is not None
        assert cached["score"] == 0.9
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


def test_cache_miss_on_content_change():
    cache_dir = tempfile.mkdtemp()
    try:
        cache = CheckerCache(cache_dir=cache_dir)
        result = {"issues": [], "score": 0.9}
        cache.set("test_checker", 1, "旧内容", result)
        cached = cache.get("test_checker", 1, "新内容")
        assert cached is None
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)


def test_cache_expiry():
    cache_dir = tempfile.mkdtemp()
    try:
        cache = CheckerCache(cache_dir=cache_dir)
        result = {"issues": [], "score": 0.9}
        cache.set("test_checker", 1, "内容", result, ttl_seconds=0)
        cached = cache.get("test_checker", 1, "内容")
        assert cached is None
    finally:
        shutil.rmtree(cache_dir, ignore_errors=True)
