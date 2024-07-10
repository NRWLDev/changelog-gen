from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TypeVar

import dulwich
import git
from dulwich import porcelain

from changelog_gen import errors
from changelog_gen.util import timer

logger = logging.getLogger(__name__)

T = TypeVar("T", bound="Git")


class Git:
    """VCS implementation for git repositories."""

    @timer
    def __init__(  # noqa: PLR0913
        self: T,
        *,
        commit: bool = True,
        release: bool = True,
        tag: bool = True,
        dry_run: bool = False,
        provider: str = "git",
    ) -> None:
        self._commit = commit
        self._release = release
        self._tag = tag
        self.dry_run = dry_run
        path = os.getenv("GIT_DIR", Path.cwd())
        self.repo = git.Repo() if provider == "git" else dulwich.repo.Repo(str(path))
        self.dulwich = dulwich.repo.Repo(str(path))
        self.provider = provider

    @timer
    def get_current_info(self: T) -> dict[str, str]:
        """Get current state info from git."""
        if self.provider == "git":
            branch = self.repo.active_branch.name
            dirty = self.repo.is_dirty()
            try:
                missing_local = list(self.repo.iter_commits(f"HEAD..origin/{branch}"))
                missing_remote = list(self.repo.iter_commits(f"origin/{branch}..HEAD"))
            except git.GitCommandError as e:
                msg = f"Unable to determine missing commit status: {e}"
                raise errors.VcsError(msg) from e
        else:
            branch = porcelain.active_branch(self.repo)

            index = self.repo.open_index()
            try:
                tree_id = self.repo[self.repo.head()].tree
            except KeyError:
                tree_id = None

            path = self.repo.path
            staged = next(index.changes_from_tree(self.repo.object_store, tree_id), None)
            unstaged = next(porcelain.get_unstaged_changes(index, path), None)
            untracked = next(porcelain.get_untracked_paths(path, path, index, path, untracked_files="all"), None)
            dirty = {staged, unstaged, untracked} != {None}
            missing_local = []
            missing_remote = []

        return {
            "missing_local": missing_local != [],
            "missing_remote": missing_remote != [],
            "dirty": dirty,
            "branch": branch,
        }

    @timer
    def find_tag(self: T, version_string: str) -> str | None:
        """Find a version tag given the version string.

        Given a version string `0.1.2` find the version tag `v0.1.2`, `0.1.2` etc.
        """
        if self.provider == "git":
            tag = self.repo.git.tag("-l", f"*{version_string}")
        else:
            tag_ = next(
                filter(lambda x: x.decode().endswith(version_string), self.repo.refs.subkeys(b"refs/tags")),
                None,
            )
            tag = tag_.decode() if tag_ else None
        return tag or None

    @timer
    def get_logs(self: T, tag: str | None) -> list:
        """Fetch logs since last tag."""
        if self.provider == "git":
            args = [f"{tag}..HEAD"] if tag else []
            logs = self.repo.git.log(
                *args,
                z=True,  # separate with \x00 rather than \n to differentiate multiline commits
                format="%h:%H:%B",  # message only
            )
            return [m.split(":", 2) for m in logs.split("\x00") if m]

        latest_commit = self.repo[self.repo.head()]
        tagged_commit = self.repo[f"refs/tags/{tag}".encode()]
        walker = self.repo.get_walker(include=[latest_commit.id, tagged_commit.id])
        print(len(list(walker)))
        return []

    @timer
    def add_paths(self: T, paths: list[str]) -> None:
        """Add path to git repository."""
        if self.dry_run:
            logger.warning("  Would add paths '%s' to Git", "', '".join(paths))
            return

        if self.provider == "git":
            self.repo.git.add(*paths, update=True)
        else:
            repo_path = Path(self.repo.path).resolve()
            relpaths = [str(Path(p).resolve().relative_to(repo_path)) for p in paths]
            self.repo.stage(relpaths)

    @timer
    def commit(self: T, current: str, new: str, tag: str, paths: list[str] | None = None) -> None:  # noqa: C901, PLR0912
        """Commit changes to git repository."""
        logger.warning("Would prepare Git commit")
        paths = paths or []

        if paths:
            self.add_paths(paths)

        msg = [
            f"Update CHANGELOG for {new}",
            f"Bump version: {current} → {new}" if self._release else "",
        ]

        message = "\n".join(msg).strip()
        if self.dry_run or not self._commit:
            logger.warning("  Would commit to Git with message '%s", message)
            return

        if self.provider == "git":
            try:
                self.repo.git.commit(message=message)
            except git.GitCommandError as e:
                msg = f"Unable to commit: {e}"
                raise errors.VcsError(msg) from e
        else:
            s = porcelain.status(self.repo)
            staged = [c for changes in s.staged.values() for c in changes]
            msg = None
            if not staged and not s.unstaged and not s.untracked:
                msg = f"Unable to commit: 'On branch {porcelain.active_branch(self.repo).decode()}\nnothing to commit, working tree clean'"  # noqa: E501
            if s.unstaged or s.untracked:
                msg = "Unable to commit: 'Changes not staged for commit'"

            if msg:
                raise errors.VcsError(msg)

            porcelain.commit(self.repo, message=message)

        if not self._tag:
            logger.warning("  Would tag with version '%s", tag)
            return

        if self.provider == "git":
            try:
                self.repo.git.tag(tag)
            except git.GitCommandError as e:
                self.revert()
                msg = f"Unable to tag: {e}"
                raise errors.VcsError(msg) from e
        else:
            t = self.find_tag(tag)
            if t is not None:
                self.revert()
                msg = f"Unable to tag: tag '{tag} already exists"
                raise errors.VcsError(msg)

            porcelain.tag_create(self.repo, tag)

    @timer
    def revert(self: T) -> None:
        """Revert a commit."""
        if self.dry_run:
            logger.warning("Would revert commit in Git")
            return
        if self.provider == "git":
            self.repo.git.reset("HEAD~1", hard=True)
        else:
            c = self.repo[self.repo.head()]
            p = self.repo[c.parents[0]]
            t = self.repo[p.tree]
            self.repo.reset_index(t.id)
