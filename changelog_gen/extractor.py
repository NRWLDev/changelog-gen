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
class Change:  # noqa: D101
    issue_ref: str
    description: str
    commit_type: str

    short_hash: str = ""
    commit_hash: str = ""
    authors: str = ""
    scope: str = ""
    breaking: bool = False

    def __lt__(self: t.Self, other: Change) -> bool:  # noqa: D105
        s = (not self.breaking, self.scope.lower() if self.scope else "zzz", self.issue_ref.lower())
        o = (not other.breaking, other.scope.lower() if other.scope else "zzz", other.issue_ref.lower())
        return s < o


SectionDict = dict[str, dict[str, Change]]


class ChangeExtractor:
    """Parse commit logs and generate section dictionaries."""

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

    @timer
    def _extract_commit_logs(
        self: t.Self,
        sections: dict[str, dict],
        current_version: str,
    ) -> None:
        # find tag from current version
        tag = self.git.find_tag(current_version)
        logs = self.git.get_logs(tag)

        # Build a conventional commit regex based on configured sections
        #   ^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\([\w\-\.]+\))?(!)?: ([\w ])+([\s\S]*)
        types = "|".join(self.type_headers.keys())
        reg = re.compile(rf"^({types})(\([\w\-\.]+\))?(!)?: (.*)([\s\S]*)")
        self.context.warning("Extracting commit log changes.")

        for i, (short_hash, commit_hash, log) in enumerate(logs):
            m = reg.match(log)
            if m:
                self.context.debug("  Parsing commit log: %s", log.strip())
                commit_type = m[1]
                scope = (m[2] or "").replace("(", "(`").replace(")", "`)")
                breaking = m[3] is not None
                description = m[4].strip()
                # Strip githubs additional link information from description.
                description = re.sub(r" \(#\d+\)$", "", description)
                details = m[5] or ""

                # Handle missing refs in commit message, skip link generation in writer
                issue_ref = f"__{i}__"
                breaking = breaking or "BREAKING CHANGE" in details

                self.context.info("  commit_type: '%s'", commit_type)
                self.context.info("  scope: '%s'", scope)
                self.context.info("  breaking: %s", breaking)
                self.context.info("  description: '%s'", description)
                self.context.info("  details: '%s'", details)

                if breaking:
                    self.context.info("  Breaking change detected:\n    %s: %s", commit_type, description)

                change = Change(
                    description=description,
                    issue_ref=issue_ref,
                    breaking=breaking,
                    scope=scope,
                    short_hash=short_hash,
                    commit_hash=commit_hash,
                    commit_type=commit_type,
                )

                for line in details.split("\n"):
                    for target, pattern in [
                        ("issue_ref", r"Refs: #?([\w-]+)"),
                        ("authors", r"Authors: (.*)"),
                    ]:
                        m = re.match(pattern, line)
                        if m:
                            self.context.info("  '%s' footer extracted '%s'", target, m[1])
                            setattr(change, target, m[1])

                header = self.type_headers.get(commit_type, commit_type)
                sections[header][change.issue_ref] = change
            elif self.include_all:
                self.context.debug("  Including non-conventional commit log (include-all): %s", log.strip())
                issue_ref = f"__{i}__"
                change = Change(
                    description=log.strip().split("\n")[0],
                    issue_ref=issue_ref,
                    breaking=False,
                    scope="",
                    short_hash=short_hash,
                    commit_hash=commit_hash,
                    commit_type="_misc",
                )
                header = self.type_headers.get(change.commit_type, change.commit_type)
                sections[header][change.issue_ref] = change

            else:
                self.context.debug("  Skipping commit log (not conventional): %s", log.strip())

    @timer
    def extract(self: t.Self, current_version: str) -> SectionDict:
        """Iterate over release note files extracting sections and issues."""
        sections = defaultdict(dict)

        self._extract_commit_logs(sections, current_version)

        return sections

    @timer
    def unique_issues(self: t.Self, sections: SectionDict) -> list[str]:
        """Generate unique list of issue references."""
        issue_refs = set()
        issue_refs = {
            issue.issue_ref
            for issues in sections.values()
            for issue in issues.values()
            if issue.commit_type in self.type_headers
        }
        return sorted(issue_refs)


@timer
def extract_semver(
    sections: SectionDict,
    context: Context,
    current: str,
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
    for section_issues in sections.values():
        for issue in section_issues.values():
            if semvers.index(semver) < semvers.index(semver_mapping.get(issue.commit_type, "patch")):
                semver = semver_mapping.get(issue.commit_type, "patch")
                context.info("'%s' change detected from commit_type '%s'", semver, issue.commit_type)
            if issue.breaking and semver != "major":
                semver = "major"
                context.info("'%s' change detected from breaking issue '%s'", semver, issue.commit_type)

    if current.startswith("0.") and semver != "patch":
        # If currently on 0.X releases, downgrade semver by one, major -> minor etc.
        idx = semvers.index(semver)
        new_ = semvers[max(idx - 1, 0)]
        context.info("'%s' change downgraded to '%s' for 0.x release.", semver, new_)
        semver = new_

    context.reset()
    return semver
