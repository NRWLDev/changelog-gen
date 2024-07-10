from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass

from bumpversion.bump import get_next_version
from bumpversion.config import get_configuration
from bumpversion.config.files import find_config_file
from bumpversion.context import get_context
from bumpversion.exceptions import ConfigurationError
from bumpversion.files import ConfiguredFile

from changelog_gen import errors
from changelog_gen.util import timer

if t.TYPE_CHECKING:
    from bumpversion.versioning.models import Version

    from changelog_gen.config import Config

logger = logging.getLogger(__name__)

T = t.TypeVar("T", bound="BumpVersion")


@dataclass
class _Version:
    raw: str
    tag: Version

    def __str__(self: t.Self) -> str:
        return self.raw


class BumpVersion:  # noqa: D101
    @timer
    def __init__(self: T, cfg: Config, new: str = "", *, allow_dirty: bool = False, dry_run: bool = False) -> None:
        self.allow_dirty = allow_dirty
        self.dry_run = dry_run
        self.config = cfg
        self.new = new

    @timer
    def get_version_info(self: T, semver: str) -> dict[str, str | Version]:
        """Get version info for a semver release."""
        if self.config.current_version != "":
            return {}

        try:
            found_config_file = find_config_file()
            config = get_configuration(found_config_file)
        except ConfigurationError as e:
            error_message = [
                "Unable to get version data from bumpversion.",
                f"error: {e}",
            ]
            msg = "\n".join(error_message)
            raise errors.VersionError(msg) from e

        ctx = get_context(config)
        version = config.version_config.parse(config.current_version)
        if self.new:
            next_version = config.version_config.parse(self.new)
            next_version_str = self.new
        else:
            next_version = get_next_version(version, config, semver, None)
            next_version_str = config.version_config.serialize(next_version, ctx)

        return {
            "current": _Version(config.current_version, version),
            "new": _Version(next_version_str, next_version),
        }

    @timer
    def replace(self: T, current: Version, version: Version) -> list[str]:  # noqa: D102
        try:
            found_config_file = find_config_file()
            config = get_configuration(found_config_file, dry_run=self.dry_run, allow_dirty=self.allow_dirty)
        except ConfigurationError as e:
            error_message = [
                "Unable to modify files with bumpversion.",
                f"error: {e}",
            ]
            msg = "\n".join(error_message)
            raise errors.VersionError(msg) from e

        configured_files = [ConfiguredFile(file_cfg, config.version_config) for file_cfg in config.files_to_modify]
        ctx = get_context(config, current, version)

        for f in configured_files:
            f.make_file_change(current, version, ctx, self.dry_run)

        return [fc.filename for fc in config.files_to_modify]
