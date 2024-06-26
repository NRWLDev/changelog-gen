from __future__ import annotations

import dataclasses
import logging
import re
import typing
from collections import defaultdict

if typing.TYPE_CHECKING:
    from changelog_gen import config
    from changelog_gen.vcs import Git
    from changelog_gen.version import BumpVersion

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Change:  # noqa: D101
    issue_ref: str
    description: str
    commit_type: str

    authors: str = ""
    scope: str = ""
    breaking: bool = False
    short_hash: str | None = None
    commit_hash: str | None = None

    def __lt__(self: typing.Self, other: Change) -> bool:  # noqa: D105
        s = (not self.breaking, self.scope.lower() if self.scope else "zzz", self.issue_ref.lower())
        o = (not other.breaking, other.scope.lower() if other.scope else "zzz", other.issue_ref.lower())
        return s < o


SectionDict = dict[str, dict[str, Change]]


class ReleaseNoteExtractor:
    """Parse release notes and generate section dictionaries."""

    def __init__(
        self: typing.Self,
        cfg: config.Config,
        git: Git,
        *,
        dry_run: bool = False,
        include_all: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self.include_all = include_all
        self.type_headers = cfg.type_headers
        if self.include_all:
            self.type_headers["_misc"] = "Miscellaneous"
        self.git = git

    def _extract_commit_logs(
        self: typing.Self,
        sections: dict[str, dict],
        current_version: str,
    ) -> None:
        # find tag from current version
        tag = self.git.find_tag(current_version)
        logs = self.git.get_logs(tag)

        # Build a conventional commit regex based on configured sections
        #   ^(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test){1}(\([\w\-\.]+\))?(!)?: ([\w ])+([\s\S]*)
        types = "|".join(self.type_headers.keys())
        reg = re.compile(rf"^({types}){{1}}(\([\w\-\.]+\))?(!)?: ([\w .,\?`\-\/]+)+([\s\S]*)")
        logger.warning("Extracting commit log changes.")

        for i, (short_hash, commit_hash, log) in enumerate(logs):
            m = reg.match(log)
            if m:
                logger.debug("  Parsing commit log: %s", log.strip())
                commit_type = m[1]
                scope = (m[2] or "").replace("(", "(`").replace(")", "`)")
                breaking = m[3] is not None
                description = m[4].strip()
                details = m[5] or ""

                # Handle missing refs in commit message, skip link generation in writer
                issue_ref = f"__{i}__"
                breaking = breaking or "BREAKING CHANGE" in details

                logger.info("  commit_type: '%s'", commit_type)
                logger.info("  scope: '%s'", scope)
                logger.info("  breaking: %s", breaking)
                logger.info("  description: '%s'", description)
                logger.info("  details: '%s'", details)

                if breaking:
                    logger.info("  Breaking change detected:\n    %s: %s", commit_type, description)

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
                            logger.info("  '%s' footer extracted '%s'", target, m[1])
                            setattr(change, target, m[1])

                header = self.type_headers.get(commit_type, commit_type)
                sections[header][change.issue_ref] = change
            elif self.include_all:
                logger.debug("  Including non-conventional commit log (include-all): %s", log.strip())
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
                logger.debug("  Skipping commit log (not conventional): %s", log.strip())

    def extract(self: typing.Self, current_version: str) -> SectionDict:
        """Iterate over release note files extracting sections and issues."""
        sections = defaultdict(dict)

        self._extract_commit_logs(sections, current_version)

        return sections

    def unique_issues(self: typing.Self, sections: SectionDict) -> list[str]:
        """Generate unique list of issue references."""
        issue_refs = set()
        issue_refs = {
            issue.issue_ref
            for issues in sections.values()
            for issue in issues.values()
            if issue.commit_type in self.type_headers
        }
        return sorted(issue_refs)


def extract_version_tag(sections: SectionDict, cfg: config.Config, bv: BumpVersion) -> str:
    """Generate new version tag based on changelog sections.

    Breaking changes: major
    Feature releases: minor
    Bugs/Fixes: patch

    """
    logger.warning("Detecting semver from changes.")
    semver_mapping = cfg.semver_mappings
    version_info_ = bv.get_version_info("patch")
    current = version_info_["current"]

    semvers = ["patch", "minor", "major"]
    semver = "patch"
    for section_issues in sections.values():
        for issue in section_issues.values():
            if semvers.index(semver) < semvers.index(semver_mapping.get(issue.commit_type, "patch")):
                semver = semver_mapping.get(issue.commit_type, "patch")
                logger.info("  '%s' change detected from commit_type '%s'", semver, issue.commit_type)
            if issue.breaking and semver != "major":
                semver = "major"
                logger.info("  '%s' change detected from breaking issue '%s'", semver, issue.commit_type)

    if current.startswith("0.") and semver != "patch":
        # If currently on 0.X releases, downgrade semver by one, major -> minor etc.
        idx = semvers.index(semver)
        new_ = semvers[max(idx - 1, 0)]
        logger.info("  '%s' change downgraded to '%s' for 0.x release.", semver, new_)
        semver = new_

    version_info = bv.get_version_info(semver)

    return version_info["new"]
