from __future__ import annotations

import contextlib
import importlib.metadata
import platform
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import rtoml
import typer
from pygments import formatters, highlight, lexers

from changelog_gen import (
    config,
    errors,
    extractor,
    writer,
)
from changelog_gen.cli import util
from changelog_gen.context import Context
from changelog_gen.util import timer
from changelog_gen.vcs import Git
from changelog_gen.version import BumpVersion

try:
    from changelog_gen.post_processor import per_issue_post_process
except ModuleNotFoundError:  # pragma: no cover
    per_issue_post_process = None

tempfile_prefix = "_tmp_changelog"


def _version_callback(*, value: bool) -> None:
    """Get current cli version."""
    if value:
        version = importlib.metadata.version("changelog-gen")
        typer.echo(f"changelog {version}")
        raise typer.Exit


def _callback(
    _version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        callback=_version_callback,
        help="Print version and exit.",
    ),
) -> None: ...


app = typer.Typer(name="changelog", callback=_callback)


@timer
def process_info(info: dict, context: Context, *, dry_run: bool) -> None:
    """Process git info and raise on invalid state."""
    if dry_run:
        return

    cfg = context.config
    if info["dirty"] and not cfg.allow_dirty:
        context.error("Working directory is not clean. Use `allow_dirty` configuration to ignore.")
        raise typer.Exit(code=1)

    if info["missing_local"] and not cfg.allow_missing:
        context.error(
            "Current local branch is missing commits from remote %s.\nUse `allow_missing` configuration to ignore.",
            info["branch"],
        )
        raise typer.Exit(code=1)

    if info["missing_remote"] and not cfg.allow_missing:
        context.error(
            "Current remote branch is missing commits from local %s.\nUse `allow_missing` configuration to ignore.",
            info["branch"],
        )
        raise typer.Exit(code=1)

    allowed_branches = cfg.allowed_branches
    if allowed_branches and info["branch"] not in allowed_branches:
        context.error("Current branch not in allowed generation branches.")
        raise typer.Exit(code=1)


@app.command("config")
def display_config() -> None:
    """Display current configuration."""
    cfg = config.read()
    typer.echo(
        highlight(
            rtoml.dumps(cfg.to_dict(), pretty=True, none_value=None),
            lexers.TOMLLexer(),
            formatters.TerminalFormatter(),
        ),
    )


@app.command("init")
def init(
    file_format: writer.Extension = typer.Option("md", help="File format to generate."),
    verbose: int = typer.Option(0, "-v", "--verbose", help="Set output verbosity.", count=True, max=3),
) -> None:
    """Generate an empty CHANGELOG file.

    Detect and raise if a CHANGELOG already exists, if not create a new file.
    """
    context = Context(config.Config(), verbose)
    extension = util.detect_extension()
    if extension is not None:
        context.error("CHANGELOG.%s detected.", extension.value)
        raise typer.Exit(code=1)

    w = writer.new_writer(context, file_format)
    w.write()


@app.command("generate")
def gen(  # noqa: PLR0913
    version_tag: Optional[str] = typer.Option(
        None,
        help="Provide the desired version tag, skip auto generation.",
        show_default=False,
    ),
    version_part: Optional[str] = typer.Option(
        None,
        help="Provide the desired version part, skip auto generation.",
        show_default=False,
    ),
    post_process_url: Optional[str] = typer.Option(
        None,
        help="Rest API endpoint to post release version notifications to.",
        show_default=False,
    ),
    post_process_auth_env: Optional[str] = typer.Option(
        None,
        help="Name of the ENV variable that contains the rest API basic auth content.",
        show_default=False,
    ),
    date_format: Optional[str] = typer.Option(
        None,
        help="The date format for strftime - empty string allowed.",
        show_default=False,
    ),
    *,
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write release notes, check for errors."),  # noqa: FBT003
    include_all: bool = typer.Option(
        False,  # noqa: FBT003
        "--include-all",
        help="Include all commits, even ones that are incorrectly formatted.",
    ),
    allow_dirty: Optional[bool] = typer.Option(
        None,
        help="Don't abort if branch contains uncommitted changes.",
        show_default=False,
    ),
    allow_missing: Optional[bool] = typer.Option(
        None,
        help="Don't abort if branch missing commits on origin.",
        show_default=False,
    ),
    reject_empty: Optional[bool] = typer.Option(
        None,
        help="Don't accept changes if there are no release notes.",
        show_default=False,
    ),
    pre_release: Optional[bool] = typer.Option(None, help="Allow/disallow pre-releases.", show_default=False),
    release: Optional[bool] = typer.Option(
        None,
        help="Update version strings in configured files.",
        show_default=False,
    ),
    commit: Optional[bool] = typer.Option(
        None,
        help="Commit changes made to changelog, and configured files, after writing.",
        show_default=False,
    ),
    tag: Optional[bool] = typer.Option(None, help="Tag changes made after release.", show_default=False),
    interactive: Optional[bool] = typer.Option(
        default=None,
        help="Open changes in an editor before confirmation.",
        show_default=False,
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically accept changes."),  # noqa: FBT003
    verbose: int = typer.Option(0, "-v", "--verbose", help="Set output verbosity.", count=True, max=3),
    _version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        help="Print version and exit.",
    ),
) -> None:
    """Generate changelog entries.

    Read release notes and generate a new CHANGELOG entry for the current version.
    """
    start = time.time()
    cfg = config.read(
        release=release,
        allow_dirty=allow_dirty,
        allow_missing=allow_missing,
        commit=commit,
        tag=tag,
        reject_empty=reject_empty,
        date_format=date_format,
        interactive=interactive,
        post_process_url=post_process_url,
        post_process_auth_env=post_process_auth_env,
        pre_release=pre_release,
        verbose=verbose,
    )
    context = Context(cfg, verbose)

    interactive = cfg.interactive
    if platform.system() == "Windows" and interactive:
        context.debug("Disabling interactive on windows.")
        interactive = False

    try:
        _gen(
            context,
            version_part,
            version_tag,
            dry_run=dry_run,
            interactive=interactive,
            include_all=include_all,
            yes=yes,
        )
    except errors.ChangelogException as ex:
        context.stacktrace()
        context.debug("Run time (error) %f", (time.time() - start) * 1000)
        context.error(str(ex))
        raise typer.Exit(code=1) from ex
    context.debug("Run time %f", (time.time() - start) * 1000)


@timer
def create_with_editor(context: Context, content: str, extension: writer.Extension) -> str:
    """Open temporary file in editor to allow modifications."""
    editor = util.get_editor()
    tmpfile = NamedTemporaryFile(
        mode="w",
        encoding="UTF-8",
        prefix=tempfile_prefix,
        suffix=f".{extension.value}",
        delete=False,
    )
    try:
        with tmpfile as f:
            f.write(content)

        editor = [part.format(tmpfile.name) for part in shlex.split(editor)]
        if not any(tmpfile.name in part for part in editor):
            editor.append(tmpfile.name)

        try:
            subprocess.call(editor)  # noqa: S603
        except OSError as e:
            context.error("Error: could not open editor!")
            raise typer.Exit(code=1) from e

        with Path(tmpfile.name).open() as f:
            content = f.read()

    finally:
        with contextlib.suppress(OSError):
            Path(tmpfile.name).unlink()

    return content


@timer
def _gen(  # noqa: PLR0913
    context: Context,
    version_part: str | None = None,
    new_version: str | None = None,
    *,
    dry_run: bool = False,
    interactive: bool = True,
    include_all: bool = False,
    yes: bool = False,
) -> None:
    cfg = context.config
    bv = BumpVersion(cfg, new_version, dry_run=dry_run, allow_dirty=cfg.allow_dirty)
    git = Git(context=context, dry_run=dry_run, commit=cfg.commit, release=cfg.release, tag=cfg.tag)

    extension = util.detect_extension()

    if extension is None:
        context.error("No CHANGELOG file detected, run `changelog init`")
        raise typer.Exit(code=1)

    process_info(git.get_current_info(), context, dry_run=dry_run)

    current = cfg.current_version
    if current == "":
        # Fetch from bumpversion until deprecated
        version_info_ = bv.get_version_info("patch")
        current = str(version_info_["current"])

    e = extractor.ChangeExtractor(context=context, git=git, dry_run=dry_run, include_all=include_all)
    sections = e.extract(current)

    unique_issues = e.unique_issues(sections)
    if not unique_issues and cfg.reject_empty:
        context.error("No changes present and reject_empty configured.")
        raise typer.Exit(code=0)

    semver = extractor.extract_semver(sections, context, current)
    semver = version_part or semver

    version_info_ = bv.get_version_info(semver)
    new = version_info_["new"]
    current = version_info_["current"]

    version_tag = cfg.version_string.format(new_version=str(new))
    version_string = version_tag

    date_fmt = cfg.date_format
    if date_fmt:
        version_string += f" {datetime.now(timezone.utc).strftime(date_fmt)}"

    w = writer.new_writer(context, extension, dry_run=dry_run)

    w.add_version(version_string)
    w.consume(cfg.type_headers, sections)

    changes = create_with_editor(context, str(w), extension) if interactive else str(w)

    # If auto accepting don't print to screen unless verbosity set
    context.error(changes) if not yes else context.warning(changes)
    w.content = changes.split("\n")[2:-2]

    processed = False
    if (
        dry_run
        or yes
        or typer.confirm(
            f"Write CHANGELOG for suggested version {new}",
        )
    ):
        paths = []
        if cfg.release:
            paths = bv.replace(current, new)

        w.write()

        paths.append(f"CHANGELOG.{extension.value}")

        git.commit(str(current), str(new), version_tag, paths)
        processed = True

    post_process = cfg.post_process
    if post_process and processed:
        # Don't import httpx unless required
        if per_issue_post_process is None:
            context.error("httpx required to execute post process, install with `--extras post-process`.")
            return

        unique_issues = [r for r in unique_issues if not r.startswith("__")]
        per_issue_post_process(context, post_process, sorted(unique_issues), str(new), dry_run=dry_run)
