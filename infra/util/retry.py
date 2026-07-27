#!/usr/bin/env python3
"""
智能重试机制

参考 opencode 的 retry.ts 设计，支持：
1. 瞬时错误检测（网络错误、超时等）
2. 指数退避重试
3. 可配置重试次数、延迟、因子、最大延迟
4. 自定义重试条件
"""

import asyncio
import random
import time
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

from infra.errors import (
    AuthenticationError, BaseError, FatalError, NetworkError, RateLimitError,
    RetryableError, ServiceUnavailableError, TimeoutError, is_instance,
)

T = TypeVar('T')


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 30.0,
        jitter: bool = True,
        retry_on_exception: Optional[Callable[[Exception], bool]] = None,
        retry_on_result: Optional[Callable[[Any], bool]] = None,
        on_retry: Optional[Callable[[int, float, Exception], None]] = None,
        backoff: str = "exponential",
    ):
        """
        初始化重试配置

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟（秒）
            factor: 延迟增长因子
            max_delay: 最大延迟（秒）
            jitter: 是否添加随机抖动
            retry_on_exception: 自定义异常重试条件
            retry_on_result: 自定义结果重试条件
            on_retry: 重试回调
            backoff: 退避策略（exponential | linear | fixed）
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.factor = factor
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_on_exception = retry_on_exception
        self.retry_on_result = retry_on_result
        self.on_retry = on_retry
        self.backoff = backoff

    def calculate_delay(self, attempt: int) -> float:
        """
        计算延迟时间

        Args:
            attempt: 当前重试次数（从0开始）

        Returns:
            延迟时间（秒）
        """
        if attempt <= 0:
            return self.base_delay

        if self.backoff == "linear":
            delay = self.base_delay * (attempt + 1)
        elif self.backoff == "fixed":
            delay = self.base_delay
        else:
            delay = self.base_delay * (self.factor ** attempt)

        delay = min(delay, self.max_delay)

        if self.jitter:
            jitter_amount = delay * 0.1
            delay = delay + random.uniform(-jitter_amount, jitter_amount)

        return max(delay, 0.1)


def is_transient_error(exc: Exception) -> bool:
    """
    判断是否为瞬时错误（可重试）

    Args:
        exc: 异常对象

    Returns:
        是否为瞬时错误
    """
    if isinstance(exc, (NetworkError, TimeoutError, ServiceUnavailableError)):
        return True

    if isinstance(exc, RetryableError):
        return True

    if isinstance(exc, RateLimitError):
        return True

    if isinstance(exc, BaseError):
        return exc.has_tag("retryable")

    if is_instance(exc, "NetworkError") or is_instance(exc, "TimeoutError"):
        return True

    exception_types = (
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
        OSError,
    )
    return isinstance(exc, exception_types)


def retry(
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    装饰器：添加重试功能

    Args:
        config: 重试配置
        **kwargs: 配置参数（覆盖config）

    Returns:
        装饰后的函数
    """
    if config is None:
        config = RetryConfig(**kwargs)
    else:
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    if config.retry_on_result and config.retry_on_result(result):
                        raise RetryableError(f"Retrying on result: {result}")

                    return result

                except Exception as exc:
                    last_exception = exc

                    if attempt >= config.max_retries:
                        raise

                    should_retry = False

                    if config.retry_on_exception:
                        should_retry = config.retry_on_exception(exc)
                    else:
                        should_retry = is_transient_error(exc)

                    if not should_retry:
                        raise

                    delay = config.calculate_delay(attempt)

                    if config.on_retry:
                        config.on_retry(attempt + 1, delay, exc)

                    time.sleep(delay)

            raise last_exception or Exception("Unknown error")

        return wrapper

    return decorator


async def retry_async(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    **kwargs,
) -> T:
    """
    异步重试

    Args:
        func: 异步函数
        config: 重试配置
        **kwargs: 函数参数

    Returns:
        函数执行结果
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            result = await func(**kwargs)

            if config.retry_on_result and config.retry_on_result(result):
                raise RetryableError(f"Retrying on result: {result}")

            return result

        except Exception as exc:
            last_exception = exc

            if attempt >= config.max_retries:
                raise

            should_retry = False

            if config.retry_on_exception:
                should_retry = config.retry_on_exception(exc)
            else:
                should_retry = is_transient_error(exc)

            if not should_retry:
                raise

            delay = config.calculate_delay(attempt)

            if config.on_retry:
                config.on_retry(attempt + 1, delay, exc)

            await asyncio.sleep(delay)

    raise last_exception or Exception("Unknown error")


def with_retry(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
) -> Callable[..., T]:
    """
    为函数添加重试功能

    Args:
        func: 函数
        config: 重试配置

    Returns:
        包装后的函数
    """
    return retry(config)(func)


def backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> float:
    """
    计算退避延迟

    Args:
        attempt: 当前重试次数
        base_delay: 基础延迟
        factor: 增长因子
        max_delay: 最大延迟
        jitter: 是否添加抖动

    Returns:
        延迟时间
    """
    delay = base_delay * (factor ** attempt)
    delay = min(delay, max_delay)

    if jitter:
        jitter_amount = delay * 0.1
        delay = delay + random.uniform(-jitter_amount, jitter_amount)

    return max(delay, 0.1)


__all__ = [
    "RetryConfig",
    "is_transient_error",
    "retry",
    "retry_async",
    "with_retry",
    "backoff_delay",
]
