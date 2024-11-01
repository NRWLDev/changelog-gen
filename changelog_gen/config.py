from __future__ import annotations

import dataclasses
import re
import string
import typing as t
from pathlib import Path

import rtoml

from changelog_gen import errors
from changelog_gen.util import timer

SUPPORTED_TYPES = {
    "feat": "Features and Improvements",
    "fix": "Bug fixes",
    "bug": "Bug fixes",
    "docs": "Documentation",
    "chore": "Miscellaneous",
    "ci": "Miscellaneous",
    "perf": "Miscellaneous",
    "refactor": "Miscellaneous",
    "revert": "Miscellaneous",
    "style": "Miscellaneous",
    "test": "Miscellaneous",
}

FOOTER_PARSERS = [
    r"(Refs)(: )(#?[\w-]+)",
    r"(Authors)(: )(.*)",
]


@dataclasses.dataclass
class PostProcessConfig:
    """Post Processor configuration options."""

    link_generator: dict[str, str] | None = None
    verb: str = "POST"
    # The body to send as a post-processing command,
    # can have the entries: ::issue_ref::, ::version::
    body_template: str = '{"body": "Released on {{ version }}"}'
    auth_type: str = "basic"  # future proof config
    headers: dict | None = None
    # Name of an environment variable to use as HTTP Basic Auth parameters.
    # The variable should contain "{user}:{api_key}"
    auth_env: str | None = None


@dataclasses.dataclass
class GithubConfig:
    """Github specific helpers."""

    strip_pr_from_description: bool = False
    extract_pr_from_description: bool = False
    extract_common_footers: bool = False


STRICT_VALIDATOR = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?$",
)


@dataclasses.dataclass
class Config:
    """Changelog configuration options."""

    current_version: str

    allowed_branches: list[str] = dataclasses.field(default_factory=list)
    commit_types: list[str] = dataclasses.field(default_factory=lambda: list(SUPPORTED_TYPES.keys()))
    type_headers: dict[str, str] = dataclasses.field(default_factory=lambda: SUPPORTED_TYPES.copy())

    # CLI overrides
    verbose: int = 0
    interactive: bool = True
    release: bool = True
    commit: bool = True
    tag: bool = True
    allow_dirty: bool = False
    allow_missing: bool = False
    reject_empty: bool = False
    statistics: bool = False

    # Version parsing
    minor_regex: str = "feat"
    parser: t.Pattern = r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    serialisers: list[str] = dataclasses.field(default_factory=lambda: ["{major}.{minor}.{patch}"])
    parts: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    strict: bool = False
    pre_release: bool = False
    pre_release_components: list[str] | None = None

    # Version bumping
    files: dict = dataclasses.field(default_factory=dict)

    # Github helpers
    github: GithubConfig | None = None

    # Changelog configuration
    date_format: str | None = None
    version_string: str = "v{new_version}"
    footer_parsers: list[str] = dataclasses.field(default_factory=lambda: FOOTER_PARSERS[::])
    # footers can be a list to simplify configuration for footers sharing related information
    extractors: list[dict[str, str | list[str]]] = dataclasses.field(default_factory=list)
    link_generators: list[dict[str, str]] = dataclasses.field(default_factory=list)
    change_template: str | None = None
    release_template: str | None = None

    # Hooks
    post_process: PostProcessConfig | None = None
    hooks: list[str] = dataclasses.field(default_factory=list)

    custom: dict = dataclasses.field(default_factory=dict)

    def __post_init__(self: t.Self) -> None:
        """Process parser and validate if strict check enabled."""
        self.parser = re.compile(self.parser)

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
                # validate that version string fits SemVer 2.0.0
                m = STRICT_VALIDATOR.match(version)
                if m is None:
                    msg = f"{serialiser} generates non SemVer 2.0.0 version string."
                    raise errors.UnsupportedSerialiserError(msg)
                serialised_keys.update([i[1] for i in string.Formatter().parse(serialiser)])

            # Validate all components covered by at least one serialiser
            missed_keys = set(configured_keys) - serialised_keys
            if missed_keys:
                msg = f"Not all parsed components handled by a serialiser, missing {missed_keys}."
                raise errors.UnsupportedSerialiserError(msg)

    def _type_to_semver(self: t.Self, commit_type: str) -> str:
        if re.match(self.minor_regex, commit_type):
            return "minor"
        return "patch"

    @property
    def semver_mappings(self: t.Self) -> dict[str, str]:
        """Generate `type: semver` mapping from commit types."""
        return {ct: self._type_to_semver(ct) for ct in self.commit_types}

    def to_dict(self: Config) -> dict:
        """Convert a Config object to a dictionary of key value pairs."""
        data = dataclasses.asdict(self)
        data["parser"] = data["parser"].pattern
        ret = {k: v for k, v in data.items() if k not in ("files", "link_generators", "extractors")}
        ret["files"] = data.get("files")
        ret["link_generators"] = data.get("link_generators")
        ret["extractors"] = data.get("extractors")

        return ret


@timer
def _process_overrides(overrides: dict) -> dict:
    """Process provided overrides.

    Remove any unsupplied values (None).
    """
    return {k: v for k, v in overrides.items() if v is not None}


@timer
def _process_pyproject(pyproject: Path) -> dict:
    cfg = {}
    with pyproject.open() as f:
        data = rtoml.load(f)

        if "tool" not in data or "changelog_gen" not in data["tool"]:
            return cfg

        footer_parsers = FOOTER_PARSERS[::]
        footer_parsers.extend(data["tool"]["changelog_gen"].get("footer_parsers", []))

        type_headers = SUPPORTED_TYPES.copy()
        type_headers_ = data["tool"]["changelog_gen"].get("commit_types", {})
        type_headers.update({v["type"]: v["header"] for v in type_headers_})
        commit_types = list(type_headers.keys())

        data["tool"]["changelog_gen"]["footer_parsers"] = footer_parsers
        data["tool"]["changelog_gen"]["commit_types"] = commit_types
        data["tool"]["changelog_gen"]["type_headers"] = type_headers

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
    overrides = _process_overrides(kwargs)
    cfg = {}

    pyproject = Path(path)

    if not pyproject.exists():
        msg = "pyproject.toml configuration missing."
        raise errors.ChangelogException(msg)

    # parse pyproject
    cfg = _process_pyproject(pyproject)

    cfg.update(overrides)

    check_deprecations(cfg)  # pragma: no mutate

    if cfg.get("post_process"):
        pp = cfg["post_process"]
        try:
            cfg["post_process"] = PostProcessConfig(**pp)
        except Exception as e:
            msg = f"Failed to create post_process: {e!s}"
            raise RuntimeError(msg) from e

    if "github" in cfg:
        github = GithubConfig(**cfg["github"])
        cfg["github"] = github

    try:
        return Config(**cfg)
    except TypeError as e:
        msg = "Invalid configuration."
        raise errors.ChangelogException(msg) from e
