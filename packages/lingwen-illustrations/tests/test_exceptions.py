"""Test custom exception hierarchy for illustrations pipeline."""

from lingwen_illustrations.exceptions import (
    ComposeError,
    ExtractError,
    GenerateError,
    IllustrationError,
    LoadError,
    Stage,
    StoreError,
)


def test_stage_enum_values():
    assert Stage.LOAD == "load"
    assert Stage.EXTRACT == "extract"
    assert Stage.COMPOSE == "compose"
    assert Stage.GENERATE == "generate"
    assert Stage.STORE == "store"


def test_base_error_includes_stage_and_retryable():
    err = IllustrationError(Stage.LOAD, "chapter not found", retryable=False)
    assert err.stage == Stage.LOAD
    assert str(err) == "[load] chapter not found"
    assert err.retryable is False


def test_subclass_default_retryable():
    assert LoadError("x").retryable is False
    assert ExtractError("x").retryable is True
    assert ComposeError("x").retryable is False
    assert GenerateError("x", retry_after=30).retryable is True
    assert GenerateError("x", retry_after=30).retry_after == 30
    assert StoreError("x").retryable is False


def test_subclass_inherits_stage():
    assert LoadError("x").stage == Stage.LOAD
    assert ExtractError("x").stage == Stage.EXTRACT
    assert ComposeError("x").stage == Stage.COMPOSE
    assert GenerateError("x").stage == Stage.GENERATE
    assert StoreError("x").stage == Stage.STORE
