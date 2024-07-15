from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass
from pathlib import Path
from warnings import warn

try:
    from bumpversion.bump import get_next_version
    from bumpversion.config import get_configuration
    from bumpversion.config.files import find_config_file
    from bumpversion.context import get_context
    from bumpversion.exceptions import ConfigurationError
    from bumpversion.files import ConfiguredFile
except ImportError:  # pragma: no cover
    pass

from changelog_gen import errors, parse
from changelog_gen.util import timer

if t.TYPE_CHECKING:
    try:
        from bumpversion.versioning.models import Version as BVVersion
    except ImportError:  # pragma: no cover

        class BVVersion:
            """Type check placeholder."""

    from changelog_gen.config import Config

logger = logging.getLogger(__name__)

T = t.TypeVar("T", bound="BumpVersion")


@dataclass
class ModifyFile:
    """Configured file for modification."""

    filename: str
    path: Path
    patterns: list[str]

    def update(self: t.Self, current: str, new: str, *, dry_run: bool) -> tuple[Path, Path]:
        """Update file with configured patterns."""
        try:
            with self.path.open("r") as f:
                contents = f.read()
        except FileNotFoundError as e:
            msg = f"Configured file not found '{self.filename}'."
            raise errors.VersionError(msg) from e

        for pattern in self.patterns:
            try:
                search, replace = pattern.format(version=current), pattern.format(version=new)
            except KeyError as e:
                msg = f"Incorrect pattern '{pattern}' for '{self.filename}'."
                raise errors.VersionError(msg) from e

            if search == replace:
                msg = f"Pattern '{pattern}' generated no change for '{self.filename}'."
                raise errors.VersionError(msg)

            new_contents = contents.replace(search, replace)
            if new_contents == contents:
                msg = f"No change for '{self.filename}', ensure pattern '{pattern}' is correct."
                raise errors.VersionError(msg)
            contents = new_contents

        backup = Path(f"{self.path}.bak")
        if not dry_run:
            with backup.open("w") as f:
                f.write(contents)

        return (self.path, backup)


@dataclass
class Version:
    """Version string container."""

    raw: str
    tag: BVVersion

    def __str__(self: t.Self) -> str:
        """Convert version wrapper to string."""
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
        if self.config.current_version == "":
            try:
                find_config_file  # noqa: B018
            except NameError as e:  # pragma: no cover
                warn(
                    "bump-my-version is being deprecated, to continue using it install with `extras=bump-my-version`, or migrate to [tool.changelog_gen] configuration.",
                    FutureWarning,
                    stacklevel=2,
                )
                msg = "Unable to determine the current version."
                raise errors.VersionError(msg) from e

            warn(
                "bump-my-version support will be dropped in a future version, please move configuration to [tool.changelog_gen].",
                FutureWarning,
                stacklevel=2,
            )
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
                "current": Version(config.current_version, version),
                "new": Version(next_version_str, next_version),
            }

        current_version = parse.parse(self.config.parser, self.config.current_version)
        next_version = (
            parse.parse(self.config.parser, self.new)
            if self.new
            else parse.bump(
                current_version,
                semver,
                self.config.parts or {},
                self.config.pre_release_components,
                pre_release=self.config.pre_release,
            )
        )
        return {
            "current": Version(self.config.current_version, None),
            "new": Version(parse.serialise(self.config.serialisers, next_version), None),
        }

    @timer
    def replace(self: T, current: Version, version: Version) -> list[str]:  # noqa: D102, C901
        if self.config.current_version == "":
            try:
                find_config_file  # noqa: B018
            except NameError as e:  # pragma: no cover
                msg = "bump-my-version is being deprecated, to continue using it install with `extras=bump-my-version`."
                raise errors.ChangelogException(msg) from e

            warn(
                "bump-my-version support will be dropped in a future version, please move configuration to [tool.changelog_gen].",
                FutureWarning,
                stacklevel=2,
            )
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
            ctx = get_context(config, current.tag, version.tag)

            for f in configured_files:
                f.make_file_change(current.tag, version.tag, ctx, self.dry_run)

            return [fc.filename for fc in config.files_to_modify]

        cwd = Path.cwd()
        files_to_modify = {
            "pyproject.toml": ModifyFile("pyproject.toml", cwd / "pyproject.toml", ['current_version = "{version}"']),
        }
        for file in self.config.files:
            mf = files_to_modify.get(file["filename"], ModifyFile(file["filename"], cwd / file["filename"], []))
            mf.patterns.append(file.get("pattern", "{version}"))
            files_to_modify[file["filename"]] = mf

        modified_files = []
        for file in files_to_modify.values():
            try:
                modified_files.append(file.update(current.raw, version.raw, dry_run=self.dry_run))
            except Exception:  # noqa: PERF203
                if not self.dry_run:
                    for _original, backup in modified_files:
                        backup.unlink()
                raise

        if not self.dry_run:
            for original, backup in modified_files:
                original.write_text(backup.read_text())
                backup.unlink()

        return sorted({mf.filename for mf in files_to_modify.values()})
