from __future__ import annotations

import io
import sys
import traceback
import typing as t
from enum import IntEnum

import click

if t.TYPE_CHECKING:
    from changelog_gen.config import Config


class Verbosity(IntEnum):
    """Verbosity levels."""

    quiet = 0
    verbose1 = 1
    verbose2 = 2
    verbose3 = 3


class Context:
    """Global context class."""

    def __init__(self: t.Self, cfg: Config, verbose: int = 0) -> None:
        self.config = cfg
        self._verbose = verbose
        self._indent = 0

    def reset(self: t.Self) -> None:
        """Reset context messaging indentation."""
        self._indent = 0

    def indent(self: t.Self) -> None:
        """Indent context messaging."""
        self._indent += 1

    def dedent(self: t.Self) -> None:
        """Dedent context messaging."""
        self._indent = max(0, self._indent - 1)

    def _echo(self: t.Self, message: str, *args) -> None:
        """Echo to the console."""
        message = message % args
        click.echo(f"{'  ' * self._indent}{message}")

    def error(self: t.Self, message: str, *args) -> None:
        """Echo to the console."""
        self._echo(message, *args)

    def warning(self: t.Self, message: str, *args) -> None:
        """Echo to the console for -v."""
        if self._verbose > Verbosity.quiet:
            self._echo(message, *args)

    def info(self: t.Self, message: str, *args) -> None:
        """Echo to the console for -vv."""
        if self._verbose > Verbosity.verbose1:
            self._echo(message, *args)

    def debug(self: t.Self, message: str, *args) -> None:
        """Echo to the console for -vvv."""
        if self._verbose > Verbosity.verbose2:
            self._echo(message, *args)

    def stacktrace(self: t.Self) -> None:
        """Echo exceptions to console for -vvv."""
        if self._verbose > Verbosity.verbose2:
            t, v, tb = sys.exc_info()
            sio = io.StringIO()
            traceback.print_exception(t, v, tb, None, sio)
            s = sio.getvalue()
            # Clean up odd python 3.11, 3.12 formatting on mac
            s = s.replace("\n    ^^^^^^^^^^^^^^^^^^^^^^^^^^", "")
            sio.close()
            self._echo(s)
