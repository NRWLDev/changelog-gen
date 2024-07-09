from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, TypeVar

from bumpversion.bump import get_next_version
from bumpversion.config import get_configuration
from bumpversion.config.files import find_config_file
from bumpversion.context import get_context
from bumpversion.exceptions import ConfigurationError
from bumpversion.files import ConfiguredFile

from changelog_gen import errors
from changelog_gen.util import timer

if TYPE_CHECKING:
    from bumpversion.versioning.models import Version
logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BumpVersion")


@timer
def parse_info(semver: str, lines: list[str]) -> tuple[str, str]:
    """Parse output from bump-my-version info command."""
    # Handle warning if setup.cfg exists
    if lines[0] == "WARNING:":
        lines = lines[4:]
    reg = re.compile(rf".*({semver}) [-]+ (.*)")

    current = lines[0].split(" -- ")[0].strip()
    for line in lines:
        m = reg.match(line)
        if m:
            new = m[2].strip()

    return current, new


@timer
def generate_verbosity(verbose: int = 0) -> list[str]:
    """Generate verbose flags correctly for each supported bumpversion library."""
    return [f"-{'v' * verbose}"]


ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


class BumpVersion:  # noqa: D101
    @timer
    def __init__(self: T, verbose: int = 0, *, allow_dirty: bool = False, dry_run: bool = False) -> None:
        self.verbose = verbose
        self.allow_dirty = allow_dirty
        self.dry_run = dry_run

    @timer
    def _version_info_cmd(self: T) -> list[str]:
        return ["bump-my-version", "show-bump", "--ascii"]

    @timer
    def _modify_cmd(self: T, version: str) -> list[str]:
        args = ["bump-my-version", "replace", "--new-version", version]
        if self.verbose:
            args.extend(generate_verbosity(self.verbose))
        if self.dry_run:
            args.append("--dry-run")
        if self.allow_dirty:
            args.append("--allow-dirty")
        return args

    def escape_ansi(self: T, line: str) -> str:
        """Strip color codes from a string."""
        line = line.encode("ascii", errors="ignore").decode()
        line = re.sub(r"[\+\-|]", "", line)
        line = re.sub(r"\s+\n", "\n", line)
        return ansi_escape.sub("", line).strip()

    def _process_error_output(self: T, output: str) -> str:
        """Parse rich formatted error outputs to a simple string.

        Extract `Error` from rich format outputs
        ```
        Usage: bump-my-version bump [OPTIONS] [ARGS]..."),

        Try 'bump-my-version bump -h' for help"),
        ╭─ Error ──────────────────────────────────────────────────────────────────────╮"),
        │ Unable to determine the current version.                                     │"),
        ╰──────────────────────────────────────────────────────────────────────────────╯"),
        ```

        Extracted error above would be `error: Unable to determine the current version.`
        """
        error = False
        error_details = []
        # Parse rich text format cli output
        for line in output.decode().split("\n"):
            # Strip out rich text formatting
            raw = self.escape_ansi(line)
            # If we've seen `- Error ---` line already, extract error details.
            if error and raw:
                error_details.append(raw)
            error = error or raw == "Error"
            logger.warning(line.strip())
        nl = "\n"
        return f"error: {nl.join(error_details)}"

    @timer
    def get_version_info(self: T, semver: str) -> dict[str, str | Version]:
        """Get version info for a semver release."""
        command = self._version_info_cmd()
        try:
            found_config_file = find_config_file()
            config = get_configuration(found_config_file)
        except ConfigurationError as e:
            error_message = [
                "Unable to modify files with bumpversion.",
                f"cmd: {' '.join(command)}",
                f"error: {e}",
            ]
            msg = "\n".join(error_message)
            raise errors.VersionError(msg) from e

        ctx = get_context(config)
        version = config.version_config.parse(config.current_version)
        next_version = get_next_version(version, config, semver, None)
        version_str = config.version_config.serialize(version, ctx)
        next_version_str = config.version_config.serialize(next_version, ctx)

        return {
            "current": version,
            "current_str": version_str,
            "new": next_version,
            "new_str": next_version_str,
        }

    @timer
    def modify(self: T, current: Version, version: Version) -> list[str]:  # noqa: D102
        command = self._modify_cmd(version)
        try:
            found_config_file = find_config_file()
            config = get_configuration(found_config_file, dry_run=self.dry_run, allow_dirty=self.allow_dirty)
        except ConfigurationError as e:
            error_message = [
                "Unable to modify files with bumpversion.",
                f"cmd: {' '.join(command)}",
                f"error: {e}",
            ]
            msg = "\n".join(error_message)
            raise errors.VersionError(msg) from e

        configured_files = [ConfiguredFile(file_cfg, config.version_config) for file_cfg in config.files_to_modify]
        ctx = get_context(config, current, version)

        for f in configured_files:
            f.make_file_change(current, version, ctx, self.dry_run)

        return [fc.filename for fc in config.files_to_modify]
