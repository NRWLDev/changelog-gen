from unittest import mock

import pytest

from changelog_gen.context import Context


def test_indent():
    c = Context(mock.Mock())
    c.indent()

    assert c._indent == 1


def test_dedent():
    c = Context(mock.Mock())
    c._indent = 2
    c.dedent()

    assert c._indent == 1


def test_reset():
    c = Context(mock.Mock())
    c._indent = 2
    c.reset()

    assert c._indent == 0


@pytest.mark.parametrize("verbosity", [0, 1, 2, 3])
def test_verbosity(verbosity, monkeypatch):
    monkeypatch.setattr(Context, "_echo", mock.Mock())
    c = Context(mock.Mock(), verbosity)

    messages = [
        "error",
        "warning",
        "info",
        "debug",
    ]
    for message in messages:
        getattr(c, message)(message)

    assert c._echo.call_args_list == [mock.call(message) for message in messages[: verbosity + 1]]
