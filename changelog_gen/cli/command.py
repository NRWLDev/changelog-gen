from __future__ import annotations

import contextlib
import importlib
import importlib.metadata
import platform
import shlex
import subprocess
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

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
    _version: bool | None = typer.Option(  # noqa: FBT001
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
def display_config(
    key: str | None = typer.Option(
        None,
        help="Specific config key to display.",
        show_default=False,
    ),
) -> None:
    """Display current configuration."""
    cfg = config.read()
    output = cfg.to_dict()
    if key:
        output = {key: output[key]}
    typer.echo(
        highlight(
            rtoml.dumps(output, pretty=True, none_value=None),
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
    context = Context(config.Config(current_version="0.0.0"), verbose)
    extension = util.detect_extension()
    if extension is not None:
        context.error("CHANGELOG.%s detected.", extension.value)
        raise typer.Exit(code=1)

    w = writer.new_writer(context, file_format)
    w.write()


@app.command("generate")
def gen(  # noqa: PLR0913
    version_tag: str | None = typer.Option(
        None,
        help="Provide the desired version tag, skip auto generation.",
        show_default=False,
    ),
    version_part: str | None = typer.Option(
        None,
        help="Provide the desired version part, skip auto generation.",
        show_default=False,
    ),
    post_process_url: str | None = typer.Option(
        None,
        help="Rest API endpoint to post release version notifications to.",
        show_default=False,
    ),
    post_process_auth_env: str | None = typer.Option(
        None,
        help="Name of the ENV variable that contains the rest API basic auth content.",
        show_default=False,
    ),
    date_format: str | None = typer.Option(
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
    allow_dirty: bool | None = typer.Option(
        None,
        help="Don't abort if branch contains uncommitted changes.",
        show_default=False,
    ),
    allow_missing: bool | None = typer.Option(
        None,
        help="Don't abort if branch missing commits on origin.",
        show_default=False,
    ),
    reject_empty: bool | None = typer.Option(
        None,
        help="Don't accept changes if there are no release notes.",
        show_default=False,
    ),
    pre_release: bool | None = typer.Option(None, help="Allow/disallow pre-releases.", show_default=False),
    release: bool | None = typer.Option(
        None,
        help="Update version strings in configured files.",
        show_default=False,
    ),
    commit: bool | None = typer.Option(
        None,
        help="Commit changes made to changelog, and configured files, after writing.",
        show_default=False,
    ),
    tag: bool | None = typer.Option(None, help="Tag changes made after release.", show_default=False),
    statistics: bool | None = typer.Option(
        None,
        help="Capture and output statistics to screen.",
    ),
    interactive: bool | None = typer.Option(
        default=None,
        help="Open changes in an editor before confirmation.",
        show_default=False,
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Automatically accept changes."),  # noqa: FBT003
    verbose: int = typer.Option(0, "-v", "--verbose", help="Set output verbosity.", count=True, max=3),
    _version: bool | None = typer.Option(
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
        statistics=statistics,
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
    tmpfile = NamedTemporaryFile(  # noqa: SIM115
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
def _gen(  # noqa: PLR0913, C901, PLR0915
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

    e = extractor.ChangeExtractor(context=context, git=git, dry_run=dry_run, include_all=include_all)
    changes = e.extract()
    stats = e.statistics

    if not changes and cfg.reject_empty:
        context.error("No changes present and reject_empty configured.")
        raise typer.Exit(code=0)

    semver = extractor.extract_semver(changes, context)
    semver = version_part or semver

    version_info_ = bv.get_version_info(semver)
    new = version_info_["new"]
    current = version_info_["current"]

    version_tag = cfg.version_string.format(new_version=str(new))
    version_string = version_tag

    date_fmt = cfg.date_format
    if date_fmt:
        version_string += f" {datetime.now(timezone.utc).strftime(date_fmt)}"

    w = writer.new_writer(context, extension, dry_run=dry_run, change_template=cfg.change_template)

    w.consume(version_string, cfg.type_headers, changes)

    change_lines = create_with_editor(context, str(w), extension) if interactive else str(w)

    # If auto accepting don't print to screen unless verbosity set
    context.error(change_lines.replace("%", "%%")) if not yes else context.warning(change_lines.replace("%", "%%"))
    w.content = change_lines.split("\n")[2:-2]

    def changelog_hook(_context: Context, _new_version: str) -> list[str]:
        changelog_path = w.write()
        return [changelog_path]

    def release_hook(_context: Context, new_version: str) -> list[str]:
        if cfg.release:
            return bv.replace(new_version)
        return []

    hooks = [release_hook, changelog_hook]
    for hook in cfg.hooks:
        try:
            import_path, hook_func = hook.split(":")
        except ValueError as e:
            context.error("Invalid hook format, expected `path.to.module:hook_func`.")
            raise typer.Exit(code=1) from e

        try:
            mod = importlib.import_module(import_path)
        except ModuleNotFoundError as e:
            context.error("Invalid hook module `%s`, not found.", import_path)
            raise typer.Exit(code=1) from e

        try:
            hooks.append(getattr(mod, hook_func))
        except AttributeError as e:
            context.error("Invalid hook func `%s`, not found in hook module.", hook_func)
            raise typer.Exit(code=1) from e

    processed = False
    if (
        dry_run
        or yes
        or typer.confirm(
            f"Write CHANGELOG for suggested version {new}",
        )
    ):
        paths = []
        for hook in hooks:
            hook_paths = hook(context, new)
            paths.extend(hook_paths)

        git.commit(current, new, version_tag, paths)
        processed = True

    post_process = cfg.post_process
    if post_process and processed:
        # Don't import httpx unless required
        if per_issue_post_process is None:
            context.error("httpx required to execute post process, install with `--extras post-process`.")
            return

        per_issue_post_process(context, post_process, changes, str(new), dry_run=dry_run)

    if cfg.statistics:
        stats_output = f"""
# Commit Statistics

* {stats["commits"]} commits contributed to the release.
* {stats["conventional"]} commits were parsed as conventional.
        """
        context.error(stats_output)


class TemplateType(Enum):
    """Template types available for test command."""

    change = "change"
    release = "release"


@app.command("test")
def template_test(
    commit_hash: str,
    template: TemplateType = typer.Option("change", help="Template type to test."),
    file_format: writer.Extension = typer.Option("md", help="File format to test."),
    verbose: int = typer.Option(0, "-v", "--verbose", help="Set output verbosity.", count=True, max=3),
) -> None:
    """Test a change or release template."""
    cfg = config.read()
    context = Context(cfg, verbose)
    git = Git(context=context)
    if template == TemplateType.change:
        log = git.get_log(commit_hash)
        e = extractor.ChangeExtractor(context=context, git=git)
        c = e.process_log(*log)
        w = writer.new_writer(context, file_format)
        context.error(w._render_change(c))  # noqa: SLF001
    else:
        logs = git.get_logs(commit_hash)
        e = extractor.ChangeExtractor(context=context, git=git)
        w = writer.new_writer(context, file_format)
        changes = []
        for log in logs:
            c = e.process_log(*log)
            if c is not None:
                c.rendered = w._render_change(c)  # noqa: SLF001
                changes.append(c)

        w.consume("v0.0.0", cfg.type_headers, changes)
        context.error("\n".join(w.content))
