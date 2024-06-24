import logging
import re
import subprocess
from typing import TypeVar

from bumpversion import bump  # noqa: F401

from changelog_gen import errors

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="BumpVersion")


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


def generate_verbosity(verbose: int = 0) -> list[str]:
    """Generate verbose flags correctly for each supported bumpversion library."""
    return [f"-{'v' * verbose}"]


commands = {
    "get_version_info": ["bump-my-version", "show-bump", "--ascii"],
    "release": ["bump-my-version", "bump", "patch", "--new-version", "VERSION"],
    "parser": parse_info,
}


class BumpVersion:  # noqa: D101
    def __init__(self: T, verbose: int = 0, *, allow_dirty: bool = False, dry_run: bool = False) -> None:
        self.verbose = verbose
        self.allow_dirty = allow_dirty
        self.dry_run = dry_run

    def _version_info_cmd(self: T, semver: str) -> list[str]:
        command = commands["get_version_info"]
        return [c.replace("SEMVER", semver) for c in command]

    def _release_cmd(self: T, version: str) -> list[str]:
        command = commands["release"]
        args = [c.replace("VERSION", version) for c in command]
        if self.verbose:
            args.extend(generate_verbosity(self.verbose))
        if self.dry_run:
            args.append("--dry-run")
        if self.allow_dirty:
            args.append("--allow-dirty")
        return args

    def get_version_info(self: T, semver: str) -> dict[str, str]:
        """Get version info for a semver release."""
        try:
            describe_out = (
                subprocess.check_output(
                    self._version_info_cmd(semver),  # noqa: S603
                    stderr=subprocess.STDOUT,
                )
                .decode()
                .strip()
                .split("\n")
            )
        except subprocess.CalledProcessError as e:
            for line in e.output.decode().split("\n"):
                logger.warning(line.strip())
            msg = "Unable to get version data from bumpversion."
            raise errors.VersionDetectionError(msg) from e

        current, new = commands["parser"](semver, describe_out)
        return {
            "current": current,
            "new": new,
        }

    def release(self: T, version: str) -> None:
        """Generate new release."""
        try:
            describe_out = (
                subprocess.check_output(
                    self._release_cmd(version),  # noqa: S603
                    stderr=subprocess.STDOUT,
                )
                .decode()
                .strip()
                .split("\n")
            )
        except subprocess.CalledProcessError as e:
            for line in e.output.decode().split("\n"):
                logger.warning(line.strip())
            raise

        for line in describe_out:
            logger.warning(line)
