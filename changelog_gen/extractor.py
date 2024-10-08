from __future__ import annotations

import dataclasses
import re
import typing as t
from collections import defaultdict

from changelog_gen.util import timer

if t.TYPE_CHECKING:
    from changelog_gen.context import Context
    from changelog_gen.vcs import Git


@dataclasses.dataclass
class Footer:  # noqa: D101
    footer: str
    separator: str
    value: str


@dataclasses.dataclass
class Link:  # noqa: D101
    text: str
    link: str


@dataclasses.dataclass
class Change:  # noqa: D101
    header: str
    description: str
    commit_type: str

    short_hash: str = ""
    commit_hash: str = ""
    scope: str = ""
    breaking: bool = False
    footers: list[Footer] = dataclasses.field(default_factory=list)
    extractions: dict[str, list[str]] = dataclasses.field(default_factory=dict)
    links: list[Link] = dataclasses.field(default_factory=list)
    rendered: str = ""  # This is populated by the writer at run time

    def __lt__(self: t.Self, other: Change) -> bool:  # noqa: D105
        s = (not self.breaking, self.scope.lower() if self.scope else "zzz", self.issue_ref.lower())
        o = (not other.breaking, other.scope.lower() if other.scope else "zzz", other.issue_ref.lower())
        return s < o

    @property
    def issue_ref(self: t.Self) -> str:
        """Extract issue ref from footers."""
        for footer in self.footers:
            if footer.footer.lower() in ("refs", "closes", "fixes"):
                return footer.value
        return ""


class ChangeExtractor:
    """Parse commit logs and generate change list."""

    @timer
    def __init__(
        self: t.Self,
        context: Context,
        git: Git,
        *,
        dry_run: bool = False,
        include_all: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.include_all = include_all
        self.type_headers = context.config.type_headers
        if self.include_all:
            self.type_headers["_misc"] = "Miscellaneous"
        self.git = git
        self.context = context
        self._statistics = defaultdict(int)

        # Build a conventional commit regex based on configured types
        #   ^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\([\w\-\.]+\))?(!)?: ([\w ])+([\s\S]*)
        types = "|".join(self.type_headers.keys())
        self.reg = re.compile(rf"^({types})(\([\w\-\.]+\))?(!)?: (.*)([\s\S]*)", re.IGNORECASE)

    def process_log(self, short_hash: str, commit_hash: str, log: str) -> Change | None:  # noqa: C901, PLR0912, PLR0915
        """Process a commit log into a Change object."""
        m = self.reg.match(log)
        if m:
            self._statistics["conventional"] += 1
            self.context.debug("  Parsing commit log: %s", log.strip())
            footers = {}

            commit_type = m[1].lower()
            scope = (m[2] or "").replace("(", "").replace(")", "")
            breaking = m[3] is not None
            description = m[4].strip()
            prm = re.search(r"\(#\d+\)$", description)
            if prm is not None:
                # Strip githubs additional link information from description.
                if self.context.config.github and self.context.config.github.strip_pr_from_description:
                    description = re.sub(r" \(#\d+\)$", "", description)

                if self.context.config.github and self.context.config.github.extract_pr_from_description:
                    footers["pr"] = Footer("PR", ": ", prm.group()[1:-1])

            details = m[5] or ""

            # Handle missing refs in commit message, skip link generation in writer
            breaking = breaking or "BREAKING CHANGE" in details

            self.context.info("  commit_type: '%s'", commit_type)
            self.context.info("  scope: '%s'", scope)
            self.context.info("  breaking: %s", breaking)
            self.context.info("  description: '%s'", description)
            self.context.info("  details: '%s'", details)

            if breaking:
                self.context.info("  Breaking change detected:\n    %s: %s", commit_type, description)

            footer_parsers = self.context.config.footer_parsers
            if self.context.config.github and self.context.config.github.extract_common_footers:
                footer_parsers.extend([
                    r"(close)( )(#[\w-]+)",
                    r"(closes)( )(#[\w-]+)",
                    r"(closed)( )(#[\w-]+)",
                    r"(fix)( )(#[\w-]+)",
                    r"(fixes)( )(#[\w-]+)",
                    r"(fixed)( )(#[\w-]+)",
                    r"(resolve)( )(#[\w-]+)",
                    r"(resolves)( )(#[\w-]+)",
                    r"(resolved)( )(#[\w-]+)",
                ])

            for line in details.split("\n"):
                for parser in self.context.config.footer_parsers:
                    m = re.match(parser, line, re.IGNORECASE)
                    if m is not None:
                        self.context.info("  '%s' footer extracted '%s%s%s'", parser, m[1], m[2], m[3])
                        footers[m[1].lower()] = Footer(m[1], m[2], m[3])

            extractions = defaultdict(list)

            for extractor in self.context.config.extractors:
                footer_keys = extractor["footer"]
                if not isinstance(footer_keys, list):
                    footer_keys = [footer_keys]

                for fkey in footer_keys:
                    footer = footers.get(fkey.lower())
                    if footer is None:
                        continue

                    for m in re.finditer(extractor["pattern"], footer.value):
                        for k, v in m.groupdict().items():
                            extractions[k].append(v)

            header = self.type_headers.get(commit_type, commit_type)
            change = Change(
                header=header,
                description=description,
                breaking=breaking,
                scope=scope,
                short_hash=short_hash,
                commit_hash=commit_hash,
                commit_type=commit_type,
                footers=list(footers.values()),
                extractions=extractions,
            )

            links = []

            for generator in self.context.config.link_generators:
                if generator["source"] == "__change__":
                    values = [change]
                else:
                    values = extractions.get(generator["source"].lower())
                    if not values:
                        continue

                text_template = generator.get("text", "{0}")
                link_template = generator["link"]
                links.extend([Link(text_template.format(value), link_template.format(value)) for value in values])

            change.links = links
            return change

        self._statistics["nonconventional"] += 1
        if self.include_all:
            self.context.debug("  Including non-conventional commit log (include-all): %s", log.strip())
            header = self.type_headers.get("_misc", "_misc")
            return Change(
                header=header,
                description=log.strip().split("\n")[0],
                breaking=False,
                scope="",
                short_hash=short_hash,
                commit_hash=commit_hash,
                commit_type="_misc",
            )

        self.context.debug("  Skipping commit log (not conventional): %s", log.strip())

        return None

    @timer
    def extract(self: t.Self) -> list[Change]:
        """Iterate over commit logs and generate list of changes."""
        current_version = self.context.config.current_version
        # find tag from current version
        tag = self.git.find_tag(current_version)
        logs = self.git.get_logs(tag)

        self.context.warning("Extracting commit log changes.")

        self._statistics["commits"] = len(logs)
        changes = []
        for short_hash, commit_hash, log in logs:
            change = self.process_log(short_hash, commit_hash, log)
            if change is not None:
                changes.append(change)

        return changes

    @property
    def statistics(self: t.Self) -> dict[str, int]:
        """Return captures statistics during extraction."""
        return self._statistics


@timer
def extract_semver(
    changes: list[Change],
    context: Context,
) -> str:
    """Extract detected semver from commit logs.

    Breaking changes: major
    Feature releases: minor
    Bugs/Fixes: patch

    """
    context.warning("Detecting semver from changes.")
    semver_mapping = context.config.semver_mappings

    context.indent()
    semvers = ["patch", "minor", "major"]
    semver = "patch"
    for change in changes:
        if semvers.index(semver) < semvers.index(semver_mapping.get(change.commit_type, "patch")):
            semver = semver_mapping.get(change.commit_type, "patch")
            context.info("'%s' change detected from commit_type '%s'", semver, change.commit_type)
        if change.breaking and semver != "major":
            semver = "major"
            context.info("'%s' change detected from breaking change '%s'", semver, change.commit_type)

    if context.config.current_version.startswith("0.") and semver != "patch":
        # If currently on 0.X releases, downgrade semver by one, major -> minor etc.
        idx = semvers.index(semver)
        new_ = semvers[max(idx - 1, 0)]
        context.info("'%s' change downgraded to '%s' for 0.x release.", semver, new_)
        semver = new_

    context.reset()
    return semver
