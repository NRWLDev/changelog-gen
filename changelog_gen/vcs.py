from __future__ import annotations

import logging
from typing import TypeVar

import git

from changelog_gen import errors
from changelog_gen.util import timer

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="Git")


class Git:
    """VCS implementation for git repositories."""

    @timer
    def __init__(self: T, *, commit: bool = True, dry_run: bool = False) -> None:
        self._commit = commit
        self.dry_run = dry_run
        self.repo = git.Repo()

    @timer
    def get_current_info(self: T) -> dict[str, str]:
        """Get current state info from git."""
        branch = self.repo.active_branch.name
        try:
            missing_local = list(self.repo.iter_commits(f"HEAD..origin/{branch}"))
            missing_remote = list(self.repo.iter_commits(f"origin/{branch}..HEAD"))
        except git.GitCommandError as e:
            msg = f"Unable to determine missing commit status: {e}"
            raise errors.VcsError(msg) from e

        return {
            "missing_local": missing_local != [],
            "missing_remote": missing_remote != [],
            "dirty": self.repo.is_dirty(),
            "branch": branch,
        }

    @timer
    def find_tag(self: T, version_string: str) -> str | None:
        """Find a version tag given the version string.

        Given a version string `0.1.2` find the version tag `v0.1.2`, `0.1.2` etc.
        """
        for tag in self.repo.tags:
            if tag.name.endswith(version_string):
                return tag.name

        return None

    @timer
    def get_logs(self: T, tag: str | None) -> list:
        """Fetch logs since last tag."""
        args = [f"{tag}..HEAD"] if tag else []
        logs = self.repo.git.log(
            *args,
            z=True,  # separate with \x00 rather than \n to differentiate multiline commits
            format="%h:%H:%B",  # message only
        )
        return [m.split(":", 2) for m in logs.split("\x00") if m]

    @timer
    def add_path(self: T, path: str) -> None:
        """Add path to git repository."""
        if self.dry_run:
            logger.warning("  Would add path '%s' to Git", path)
            return
        self.repo.git.add(path, update=True)

    @timer
    def commit(self: T, version: str, paths: list[str] | None = None) -> None:
        """Commit changes to git repository."""
        logger.warning("Would prepare Git commit")
        paths = paths or []

        for path in paths:
            self.add_path(path)

        if self.dry_run or not self._commit:
            logger.warning("  Would commit to Git with message 'Update CHANGELOG for %s'", version)
            return

        try:
            self.repo.git.commit(message=f"Update CHANGELOG for {version}")
        except git.GitCommandError as e:
            msg = f"Unable to commit: {e}"
            raise errors.VcsError(msg) from e

    @timer
    def revert(self: T) -> None:
        """Revert a commit."""
        if self.dry_run:
            logger.warning("Would revert commit in Git")
            return
        self.repo.git.reset("HEAD~1", hard=True)
