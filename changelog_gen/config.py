from __future__ import annotations

import dataclasses
import json
import re
import string
import typing as t
from pathlib import Path

import rtoml

from changelog_gen import errors
from changelog_gen.util import timer


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
    ),
    "bug": CommitType(
        header="Bug fixes",
    ),
    "docs": CommitType(
        header="Documentation",
    ),
    "chore": CommitType(
        header="Miscellaneous",
    ),
    "ci": CommitType(
        header="Miscellaneous",
    ),
    "perf": CommitType(
        header="Miscellaneous",
    ),
    "refactor": CommitType(
        header="Miscellaneous",
    ),
    "revert": CommitType(
        header="Miscellaneous",
    ),
    "style": CommitType(
        header="Miscellaneous",
    ),
    "test": CommitType(
        header="Miscellaneous",
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


STRICT_VALIDATOR = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?$",
)


@dataclasses.dataclass
class Config:
    """Changelog configuration options."""

    current_version: str = ""
    parser: t.Pattern = r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    serialisers: list[str] = dataclasses.field(default_factory=lambda: ["{major}.{minor}.{patch}"])
    parts: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    files: dict = dataclasses.field(default_factory=dict)
    strict: bool = False

    verbose: int = 0

    issue_link: str | None = None
    commit_link: str | None = None
    date_format: str | None = None
    version_string: str = "v{new_version}"

    allowed_branches: list[str] = dataclasses.field(default_factory=list)
    commit_types: dict[str, CommitType] = dataclasses.field(default_factory=lambda: SUPPORTED_TYPES)

    interactive: bool = True
    release: bool = True
    commit: bool = True
    tag: bool = True
    allow_dirty: bool = False
    allow_missing: bool = False
    reject_empty: bool = False

    pre_release: bool = False
    pre_release_components: list[str] | None = None

    post_process: PostProcessConfig | None = None

    def __post_init__(self: t.Self) -> None:
        """Process parser and validate if strict check enabled."""
        self.parser = re.compile(self.parser)
        if self.commit_types != SUPPORTED_TYPES:
            for k, v in self.commit_types.items():
                value = json.loads(v) if isinstance(v, str) else v
                ct = CommitType(**value) if isinstance(value, dict) else value
                self.commit_types[k] = ct

        if self.strict:
            parts = {component: self.parts.get(component, [0])[0] for component in self.parser.groupindex}
            # Validate major, minor, patch in regex
            configured_keys = list(parts.keys())

            if {"major", "minor", "patch"} - set(configured_keys):
                msg = "major.minor.patch, pattern required at minimum."
                raise errors.UnsupportedParserError(msg)

            if configured_keys[:3] != ["major", "minor", "patch"]:
                msg = "major.minor.patch, pattern order required."
                raise errors.UnsupportedParserError(msg)

            serialised_keys = set()

            for serialiser in self.serialisers:
                version = serialiser.format(**parts)
                # validate that version string fits RFC2119
                m = STRICT_VALIDATOR.match(version)
                if m is None:
                    msg = f"{serialiser} generates non RFC-2119 version string."
                    raise errors.UnsupportedSerialiserError(msg)
                serialised_keys.update([i[1] for i in string.Formatter().parse(serialiser)])

            # Validate all components covered by at least one serialiser
            missed_keys = set(configured_keys) - serialised_keys
            if missed_keys:
                msg = f"Not all parsed components handled by a serialiser, missing {missed_keys}."
                raise errors.UnsupportedSerialiserError(msg)

    @property
    def semver_mappings(self: t.Self) -> dict[str, str]:
        """Generate `type: semver` mapping from commit types."""
        return {ct: c.semver for ct, c in self.commit_types.items()}

    @property
    def type_headers(self: t.Self) -> dict[str, str]:
        """Generate `type: header` mapping from commit types."""
        return {ct: c.header for ct, c in self.commit_types.items()}

    def to_dict(self: Config) -> dict:
        """Convert a Config object to a dictionary of key value pairs."""
        data = dataclasses.asdict(self)
        data["parser"] = data["parser"].pattern
        ret = {k: v for k, v in data.items() if k != "files"}
        ret["files"] = data.get("files")

        return ret


@timer
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


@timer
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


@timer
def check_deprecations(cfg: dict) -> None:  # noqa: ARG001
    """Check parsed configuration dict for deprecated features."""
    # No current deprecations
    return


@timer
def read(path: str = "pyproject.toml", **kwargs) -> Config:
    """Read configuration from local environment.

    Supported configuration locations (checked in order):
    * pyproject.toml
    """
    overrides, post_process = _process_overrides(kwargs)
    cfg = {}

    pyproject = Path(path)

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

    check_deprecations(cfg)  # pragma: no mutate

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
        unsupported = sorted(set(re.findall(r"(::.*?::)", str(value)) or []) - supported)
        if unsupported:
            msg = f"""Replace string(s) ('{"', '".join(unsupported)}') not supported."""
            raise errors.UnsupportedReplaceError(msg)

    if cfg.get("post_process"):
        pp = cfg["post_process"]
        try:
            cfg["post_process"] = PostProcessConfig(**pp)
        except Exception as e:
            msg = f"Failed to create post_process: {e!s}"
            raise RuntimeError(msg) from e

    return Config(**cfg)
