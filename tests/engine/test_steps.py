from types import SimpleNamespace

import pytest

from pipeline.shared.core.checks import OK, Check
from pipeline.engine.datasets import Dataset
from pipeline.engine.steps import Context, Step, check_order, producers, write_checks
from pipeline.engine.store import Store

A, B = Dataset("a"), Dataset("b")


def _noop(ctx):
    pass


def test_check_order_accepts_needs_after_makes():
    check_order([Step("one", _noop, makes=(A,)), Step("two", _noop, needs=(A,), makes=(B,))])


def test_check_order_rejects_a_need_without_an_earlier_make():
    with pytest.raises(ValueError, match="step `two` needs `a`, made by no earlier step"):
        check_order([Step("two", _noop, needs=(A,)), Step("one", _noop, makes=(A,))])


def test_check_order_rejects_a_dataset_made_twice():
    with pytest.raises(ValueError, match="`a` is made by `one` and `two`"):
        check_order([Step("one", _noop, makes=(A,)), Step("two", _noop, makes=(A,))])


def test_check_order_rejects_duplicate_step_names():
    with pytest.raises(ValueError, match="step `one` appears twice"):
        check_order([Step("one", _noop), Step("one", _noop)])


def test_producers():
    assert producers([Step("one", _noop, makes=(A, B))]) == {"a": "one", "b": "one"}


def test_context_defaults():
    ctx = Context(store=None, config=SimpleNamespace())
    assert ctx.log is print and not hasattr(ctx, "refresh")


def test_write_checks_writes_rows(tmp_path):
    store = Store(tmp_path)
    write_checks(store, Dataset("x_checks", kind="json"), [Check("a", OK, "b")])
    assert store.read(Dataset("x_checks", kind="json")) == [{"name": "a", "status": "OK", "text": "b"}]
