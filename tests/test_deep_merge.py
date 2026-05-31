"""deep_merge unit tests — load ai-sync as a module for direct calls."""

from __future__ import annotations

import pathlib
import sys
import types

import pytest

AI_SYNC_PATH = pathlib.Path(__file__).resolve().parent.parent / "bin" / "ai-sync"


@pytest.fixture(scope="module")
def ai_sync_module():
    """Load ai-sync as a module despite its lack of .py extension.

    Must register in sys.modules before exec — the @dataclass classes inside
    ai-sync do `sys.modules.get(cls.__module__).__dict__` for annotation
    resolution; without the entry that returns None and explodes.
    """
    module = types.ModuleType("ai_sync")
    module.__file__ = str(AI_SYNC_PATH)
    sys.modules["ai_sync"] = module
    try:
        exec(compile(AI_SYNC_PATH.read_text(), str(AI_SYNC_PATH), "exec"), module.__dict__)
    except Exception:
        del sys.modules["ai_sync"]
        raise
    return module


def test_top_level_overrides(ai_sync_module):
    assert ai_sync_module.deep_merge({"a": 1}, {"a": 2}) == {"a": 2}


def test_adds_new_keys(ai_sync_module):
    assert ai_sync_module.deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_recurses_into_dicts(ai_sync_module):
    base    = {"nested": {"x": 1, "y": 2}}
    overlay = {"nested": {"y": 20, "z": 30}}
    assert ai_sync_module.deep_merge(base, overlay) == {"nested": {"x": 1, "y": 20, "z": 30}}


def test_lists_replace_not_concat(ai_sync_module):
    assert ai_sync_module.deep_merge({"l": [1, 2]}, {"l": [3]}) == {"l": [3]}


def test_dict_replacing_scalar(ai_sync_module):
    """If base has a scalar and overlay has a dict at the same key, overlay wins."""
    assert ai_sync_module.deep_merge({"x": 1}, {"x": {"a": 1}}) == {"x": {"a": 1}}


def test_does_not_mutate_inputs(ai_sync_module):
    base    = {"nested": {"a": 1}}
    overlay = {"nested": {"b": 2}}
    _ = ai_sync_module.deep_merge(base, overlay)
    assert base    == {"nested": {"a": 1}}
    assert overlay == {"nested": {"b": 2}}


def test_empty_overlay_is_identity(ai_sync_module):
    base = {"a": 1, "nested": {"b": 2}}
    assert ai_sync_module.deep_merge(base, {}) == base


def test_three_level_nesting(ai_sync_module):
    base    = {"a": {"b": {"c": 1, "d": 2}}}
    overlay = {"a": {"b": {"c": 99}}}
    assert ai_sync_module.deep_merge(base, overlay) == {"a": {"b": {"c": 99, "d": 2}}}
