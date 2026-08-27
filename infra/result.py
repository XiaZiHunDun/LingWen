from __future__ import annotations

from typing import Any, Callable, Generic, Optional, TypeVar, Union

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


class Ok(Generic[T]):
    __match_args__ = ('value',)

    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def map(self, f: Callable[[T], U]) -> 'Result[U, E]':
        try:
            return Ok(f(self._value))
        except Exception as e:
            return Err(e)

    def map_err(self, f: Callable[[Any], Any]) -> 'Result[T, Any]':
        return Ok(self._value)

    def flat_map(self, f: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        try:
            return f(self._value)
        except Exception as e:
            return Err(e)

    def or_else(self, f: Callable[[Any], T]) -> T:
        return self._value

    def unwrap(self) -> T:
        return self._value

    def unwrap_or(self, default: T) -> T:
        return self._value

    def unwrap_or_else(self, f: Callable[[Any], T]) -> T:
        return self._value

    def expect(self, msg: str) -> T:
        return self._value

    def __repr__(self) -> str:
        return f'Ok({self._value!r})'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ok):
            return self._value == other._value
        return False

    def __hash__(self) -> int:
        return hash((type(self), self._value))


class Err(Generic[E]):
    __match_args__ = ('error',)

    def __init__(self, error: E) -> None:
        self._error = error

    @property
    def error(self) -> E:
        return self._error

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def map(self, f: Callable[[Any], Any]) -> 'Result[Any, E]':
        return Err(self._error)

    def map_err(self, f: Callable[[E], Any]) -> 'Result[Any, Any]':
        try:
            return Err(f(self._error))
        except Exception as e:
            return Err(e)

    def flat_map(self, f: Callable[[Any], 'Result[Any, Any]']) -> 'Result[Any, E]':
        return Err(self._error)

    def or_else(self, f: Callable[[E], T]) -> T:
        try:
            return f(self._error)
        except Exception as e:
            raise e

    def unwrap(self) -> T:
        raise ValueError(f'Cannot unwrap Err: {self._error}')

    def unwrap_or(self, default: T) -> T:
        return default

    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        try:
            return f(self._error)
        except Exception as e:
            raise e

    def expect(self, msg: str) -> T:
        raise ValueError(f'{msg}: {self._error}')

    def __repr__(self) -> str:
        return f'Err({self._error!r})'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Err):
            return self._error == other._error
        return False

    def __hash__(self) -> int:
        return hash((type(self), self._error))


Result = Union[Ok[T], Err[E]]


def ok(value: T) -> Ok[T]:
    return Ok(value)


def err(error: E) -> Err[E]:
    return Err(error)


def wrap(f: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    def wrapper(*args: Any, **kwargs: Any) -> Result[T, Exception]:
        try:
            return Ok(f(*args, **kwargs))
        except Exception as e:
            return Err(e)
    return wrapper


def from_optional(value: Optional[T], error: E) -> Result[T, E]:
    if value is not None:
        return Ok(value)
    return Err(error)


def combine(results: list[Result[T, E]]) -> Result[list[T], E]:
    successes: list[T] = []
    for result in results:
        if result.is_err():
            return result
        successes.append(result.unwrap())
    return Ok(successes)


def either(result: Result[T, E], ok_fn: Callable[[T], U], err_fn: Callable[[E], U]) -> U:
    if result.is_ok():
        return ok_fn(result.unwrap())
    return err_fn(result.error)
