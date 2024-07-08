import logging
import re
import subprocess
from typing import TypeVar

from bumpversion import bump  # noqa: F401

from changelog_gen import errors
from changelog_gen.util import timer

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
    def _release_cmd(self: T, version: str) -> list[str]:
        args = ["bump-my-version", "bump", "patch", "--new-version", version]
        if self.verbose:
            args.extend(generate_verbosity(self.verbose))
        if self.dry_run:
            args.append("--dry-run")
        if self.allow_dirty:
            args.append("--allow-dirty")
        return args

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
            raw = line.encode("ascii", errors="ignore").decode()
            raw = re.sub(r"\s+\n", "\n", raw).strip()
            # If we've seen `- Error ---` line already, extract error details.
            if error and raw:
                error_details.append(raw)
            error = error or raw == "Error"
            logger.warning(line.strip())
        nl = "\n"
        return f"error: {nl.join(error_details)}"

    @timer
    def get_version_info(self: T, semver: str) -> dict[str, str]:
        """Get version info for a semver release."""
        command = self._version_info_cmd()
        try:
            describe_out = (
                subprocess.check_output(
                    command,  # noqa: S603
                    stderr=subprocess.STDOUT,
                )
                .decode()
                .strip()
                .split("\n")
            )
        except subprocess.CalledProcessError as e:
            error_message = [
                "Unable to get version data from bumpversion.",
                f"cmd: {' '.join(command)}",
                self._process_error_output(e.output),
            ]
            msg = "\n".join(error_message)
            raise errors.VersionError(msg) from e

        current, new = parse_info(semver, describe_out)
        return {
            "current": current,
            "new": new,
        }

    @timer
    def release(self: T, version: str) -> None:
        """Generate new release."""
        command = self._release_cmd(version)
        try:
            describe_out = (
                subprocess.check_output(
                    command,  # noqa: S603
                    stderr=subprocess.STDOUT,
                )
                .decode()
                .strip()
                .split("\n")
            )
        except subprocess.CalledProcessError as e:
            error_message = [
                "Unable to generate release with bumpversion.",
                f"cmd: {' '.join(command)}",
                self._process_error_output(e.output),
            ]
            msg = "\n".join(error_message)
            raise errors.VersionError(msg) from e

        for line in describe_out:
            logger.warning(line)
