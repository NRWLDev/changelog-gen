from __future__ import annotations

import dataclasses
import json
import logging
import re
import typing
from pathlib import Path

import rtoml

from changelog_gen import errors

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class CommitType:
    """Represent a supported commit_type."""

    header: str
    semver: str = "patch"


SUPPORTED_TYPES = {
    "feat": CommitType(
        header="Features and Improvements",
        semver="minor",
    ),
    "fix": CommitType(
        header="Bug fixes",
        semver="patch",
    ),
    "bug": CommitType(
        header="Bug fixes",
        semver="patch",
    ),
    "docs": CommitType(
        header="Documentation",
        semver="patch",
    ),
    "chore": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
    "ci": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
    "perf": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
    "refactor": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
    "revert": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
    "style": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
    "test": CommitType(
        header="Miscellaneous",
        semver="patch",
    ),
}


@dataclasses.dataclass
class PostProcessConfig:
    """Post Processor configuration options."""

    url: str | None = None
    verb: str = "POST"
    # The body to send as a post-processing command,
    # can have the entries: ::issue_ref::, ::version::
    body: str = '{"body": "Released on ::version::"}'
    auth_type: str = "basic"  # future proof config
    headers: dict | None = None
    # Name of an environment variable to use as HTTP Basic Auth parameters.
    # The variable should contain "{user}:{api_key}"
    auth_env: str | None = None

    @classmethod
    def from_dict(cls: type[PostProcessConfig], data: dict) -> PostProcessConfig:
        """Convert a dictionary of key value pairs into a PostProcessConfig object."""
        return cls(**data)


@dataclasses.dataclass
class Config:
    """Changelog configuration options."""

    verbose: int = 0

    issue_link: str | None = None
    commit_link: str | None = None
    date_format: str | None = None
    version_string: str = "v{new_version}"

    allowed_branches: list[str] = dataclasses.field(default_factory=list)
    commit_types: dict[str, CommitType] = dataclasses.field(default_factory=lambda: SUPPORTED_TYPES)

    release: bool = False
    commit: bool = False
    allow_dirty: bool = False
    allow_missing: bool = False
    reject_empty: bool = False

    post_process: PostProcessConfig | None = None

    @property
    def semver_mappings(self: typing.Self) -> dict[str, str]:
        """Generate `type: semver` mapping from commit types."""
        return {ct: c.semver for ct, c in self.commit_types.items()}

    @property
    def type_headers(self: typing.Self) -> dict[str, str]:
        """Generate `type: header` mapping from commit types."""
        return {ct: c.header for ct, c in self.commit_types.items()}

    @classmethod
    def from_dict(cls: type[Config], data: dict) -> Config:
        """Convert a dictionary of key value pairs into a Config object."""
        if "commit_types" in data:
            for k, v in data["commit_types"].items():
                value = json.loads(v) if isinstance(v, str) else v
                ct = CommitType(**value) if isinstance(value, dict) else value
                data["commit_types"][k] = ct
        return cls(**data)

    def to_dict(self: Config) -> dict:
        """Convert a Config object to a dictionary of key value pairs."""
        return dataclasses.asdict(self)


def _process_overrides(overrides: dict) -> tuple[dict, PostProcessConfig | None]:
    """Process provided overrides.

    Remove any unsupplied values (None).
    """
    post_process_url = overrides.pop("post_process_url", "")
    post_process_auth_env = overrides.pop("post_process_auth_env", None)

    post_process = None
    if post_process_url or post_process_auth_env:
        post_process = PostProcessConfig(
            url=post_process_url,
            auth_env=post_process_auth_env,
        )

    overrides = {k: v for k, v in overrides.items() if v is not None}

    return overrides, post_process


def _process_pyproject(pyproject: Path) -> dict:
    cfg = {}
    with pyproject.open() as f:
        data = rtoml.load(f)

        if "tool" not in data or "changelog_gen" not in data["tool"]:
            return cfg

        commit_types = SUPPORTED_TYPES.copy()
        commit_types.update(data["tool"]["changelog_gen"].get("commit_types", {}))
        data["tool"]["changelog_gen"]["commit_types"] = commit_types
        return data["tool"]["changelog_gen"]


def check_deprecations(cfg: dict) -> None:  # noqa: ARG001
    """Check parsed configuration dict for deprecated features."""
    # No current deprecations
    return


def read(**kwargs) -> Config:
    """Read configuration from local environment.

    Supported configuration locations (checked in order):
    * pyproject.toml
    """
    overrides, post_process = _process_overrides(kwargs)
    cfg = {}

    pyproject = Path("pyproject.toml")

    if pyproject.exists():
        # parse pyproject
        cfg = _process_pyproject(pyproject)

    if "post_process" not in cfg and post_process:
        cfg["post_process"] = {
            "url": post_process.url,
            "auth_env": post_process.auth_env,
        }

    if "post_process" in cfg and post_process:
        cfg["post_process"]["url"] = post_process.url or cfg["post_process"].get("url")
        cfg["post_process"]["auth_env"] = post_process.auth_env or cfg["post_process"].get("auth_env")

    cfg.update(overrides)

    check_deprecations(cfg)

    for replace_key_path in [
        ("issue_link",),
        ("commit_link",),
        ("post_process", "url"),
        ("post_process", "body"),
    ]:
        data, value = cfg, None
        for key in replace_key_path:
            value = data.get(key)
            if key in data:
                data = data[key]

        # check for non supported replace keys
        supported = {"::issue_ref::", "::version::", "::commit_hash::"}
        unsupported = sorted(set(re.findall(r"(::.*?::)", value or "") or []) - supported)
        if unsupported:
            msg = f"""Replace string(s) ('{"', '".join(unsupported)}') not supported."""
            raise errors.UnsupportedReplaceError(msg)

    if cfg.get("post_process"):
        pp = cfg["post_process"]
        try:
            cfg["post_process"] = PostProcessConfig.from_dict(pp)
        except Exception as e:  # noqa: BLE001
            msg = f"Failed to create post_process: {e!s}"
            raise RuntimeError(msg) from e

    return Config.from_dict(cfg)
