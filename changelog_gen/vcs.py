from __future__ import annotations

import typing as t

import git

from changelog_gen import errors
from changelog_gen.util import timer

if t.TYPE_CHECKING:
    from changelog_gen.context import Context

T = t.TypeVar("T", bound="Git")


class Git:
    """VCS implementation for git repositories."""

    @timer
    def __init__(  # noqa: PLR0913
        self: T,
        context: Context,
        *,
        commit: bool = True,
        release: bool = True,
        tag: bool = True,
        dry_run: bool = False,
    ) -> None:
        self.context = context
        self._commit = commit
        self._release = release
        self._tag = tag
        self.dry_run = dry_run
        try:
            self.repo = git.Repo()
        except git.exc.InvalidGitRepositoryError as e:
            msg = "No git repository found, please run git init."
            raise errors.VcsError(msg) from e

    @timer
    def get_current_info(self: T) -> dict[str, str]:
        """Get current state info from git."""
        branch = self.repo.active_branch.name
        try:
            missing_local = list(self.repo.iter_commits(f"HEAD..origin/{branch}"))
        except git.GitCommandError as e:
            if f"bad revision 'HEAD..origin/{branch}'" in str(e):
                missing_local = []
            else:
                msg = f"Unable to determine missing commit status: {e}"
                raise errors.VcsError(msg) from e

        try:
            missing_remote = list(self.repo.iter_commits(f"origin/{branch}..HEAD"))
        except git.GitCommandError as e:
            if f"bad revision 'origin/{branch}..HEAD'" in str(e):
                missing_remote = ["missing"]
            else:
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
        tag = self.repo.git.tag("-l", f"*{version_string}")
        return tag or None

    @timer
    def get_logs(self: T, tag: str | None) -> list:
        """Fetch logs since last tag."""
        args = [f"{tag}..HEAD"] if tag else []
        try:
            logs = self.repo.git.log(
                *args,
                z=True,  # separate with \x00 rather than \n to differentiate multiline commits
                format="%h:%H:%B",  # message only
            )
        except git.exc.GitCommandError as e:
            msg = (
                "Unable to fetch commit logs."
                if "does not have any commits yet" not in str(e)
                else "No commit logs available."
            )
            raise errors.VcsError(msg) from e
        return [m.split(":", 2) for m in logs.split("\x00") if m]

    @timer
    def add_paths(self: T, paths: list[str]) -> None:
        """Add path to git repository."""
        if self.dry_run:
            self.context.warning("  Would add paths '%s' to Git", "', '".join(paths))
            return
        self.repo.git.add(*paths, update=True)

    @timer
    def commit(self: T, current: str, new: str, tag: str, paths: list[str] | None = None) -> None:
        """Commit changes to git repository."""
        self.context.warning("Would prepare Git commit")
        paths = paths or []

        if paths:
            self.add_paths(paths)

        msg = [
            f"Update CHANGELOG for {new}",
            f"Bump version: {current} → {new}" if self._release else "",
        ]

        message = "\n".join(msg).strip()
        if self.dry_run or not self._commit:
            self.context.warning("  Would commit to Git with message '%s", message)
            return

        try:
            self.repo.git.commit(message=message)
        except git.GitCommandError as e:
            msg = f"Unable to commit: {e}"
            raise errors.VcsError(msg) from e

        if not self._tag or not self._release:
            self.context.warning("  Would tag with version '%s", tag)
            return

        try:
            self.repo.git.tag(tag)
        except git.GitCommandError as e:
            self.revert()
            msg = f"Unable to tag: {e}"
            raise errors.VcsError(msg) from e

    @timer
    def revert(self: T) -> None:
        """Revert a commit."""
        if self.dry_run:
            self.context.warning("Would revert commit in Git")
            return
        self.repo.git.reset("HEAD~1", hard=True)
