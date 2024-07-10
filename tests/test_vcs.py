from unittest import mock

import git
import pytest

from changelog_gen import errors, vcs
from changelog_gen.vcs import Git


@pytest.fixture()
def multiversion_repo(git_repo):
    path = git_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world!")

    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("initial commit")

    git_repo.api.create_tag("0.0.1")

    f.write_text("hello world! v2")
    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("update")

    git_repo.api.create_tag("0.0.2")

    return git_repo


@pytest.fixture()
def multiversion_v_repo(git_repo):
    path = git_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world!")

    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("initial commit")

    git_repo.api.create_tag("v0.0.1")

    f.write_text("hello world! v2")
    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("update")

    git_repo.api.create_tag("v0.0.2")

    return git_repo


def test_get_current_info_branch(multiversion_repo, monkeypatch):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(return_value=[]))
    path = multiversion_repo.workspace
    f = path / "hello.txt"

    f.write_text("hello world! v3")

    info = Git().get_current_info()

    assert info["branch"] == "main"


@pytest.mark.usefixtures("multiversion_repo")
def test_get_current_info_clean(monkeypatch):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(return_value=[]))
    info = Git().get_current_info()

    assert info["dirty"] is False


def test_get_current_info_dirty(multiversion_repo, monkeypatch):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(return_value=[]))
    path = multiversion_repo.workspace
    f = path / "hello.txt"

    f.write_text("hello world! v3")

    info = Git().get_current_info()

    assert info["dirty"] is True


@pytest.mark.usefixtures("multiversion_repo")
def test_get_current_info_missing_remote_branch(monkeypatch):
    monkeypatch.setattr(
        vcs.git.Repo,
        "iter_commits",
        mock.Mock(side_effect=vcs.git.GitCommandError("git iter_commits")),
    )

    with pytest.raises(errors.VcsError):
        Git().get_current_info()


@pytest.mark.usefixtures("multiversion_repo")
def test_get_current_info_missing_local(monkeypatch):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(side_effect=[["commit"], []]))

    info = Git().get_current_info()

    assert info["missing_local"] is True


@pytest.mark.usefixtures("multiversion_repo")
def test_get_current_info_missing_remote(monkeypatch):
    monkeypatch.setattr(vcs.git.Repo, "iter_commits", mock.Mock(side_effect=[[], ["commit"]]))

    info = Git().get_current_info()

    assert info["missing_remote"] is True


@pytest.mark.usefixtures("multiversion_repo")
def test_get_find_tag():
    tag = Git().find_tag("0.0.2")

    assert tag == "0.0.2"


@pytest.mark.usefixtures("multiversion_repo")
def test_get_find_tag_no_tag():
    tag = Git().find_tag("0.0.3")

    assert tag is None


@pytest.mark.usefixtures("multiversion_v_repo")
def test_get_find_tag_vtag():
    tag = Git().find_tag("0.0.2")

    assert tag == "v0.0.2"


def test_add_paths_stages_changes_for_commit(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    assert "Changes not staged for commit" in multiversion_repo.run("git status", capture=True)

    Git().add_paths(["hello.txt"])

    assert "Changes not staged for commit" not in multiversion_repo.run("git status", capture=True)


def test_add_paths_dry_run(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    Git(dry_run=True).add_paths(["hello.txt"])

    assert "Changes not staged for commit" in multiversion_repo.run("git status", capture=True)


def test_commit_adds_message_with_version_string(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")

    Git().commit("current_version", "new_version", "version_tag")

    assert (
        multiversion_repo.api.head.commit.message
        == "Update CHANGELOG for new_version\nBump version: current_version → new_version\n"
    )


def test_commit_with_paths(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    Git().commit("current_version", "new_version", "version_tag", ["hello.txt"])

    assert (
        multiversion_repo.api.head.commit.message
        == "Update CHANGELOG for new_version\nBump version: current_version → new_version\n"
    )


def test_commit_dry_run(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    Git(dry_run=True).commit("current_version", "new_version", "version_tag", ["hello.txt"])

    assert "Changes not staged for commit" in multiversion_repo.run("git status", capture=True)


def test_commit_no_changes_staged(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")

    with pytest.raises(errors.VcsError) as e:
        Git().commit("current_version", "new_version", "version_tag")

    assert "Changes not staged for commit" in str(e.value)


def test_get_logs(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")
    hash1 = str(multiversion_repo.api.head.commit)

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log 2: electric boogaloo")
    hash2 = str(multiversion_repo.api.head.commit)

    f.write_text("hello world! v5")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit(
        """Commit message 3

Formatted
""",
    )
    hash3 = str(multiversion_repo.api.head.commit)

    logs = Git().get_logs("0.0.2")
    assert logs == [
        [hash3[:7], hash3, "Commit message 3\n\nFormatted\n"],
        [hash2[:7], hash2, "commit log 2: electric boogaloo"],
        [hash1[:7], hash1, "commit log"],
    ]


@pytest.mark.usefixtures("multiversion_repo")
def test_get_logs_no_tag():
    logs = Git().get_logs(None)
    assert [log[2] for log in logs] == [
        "update",
        "initial commit",
    ]


def test_commit(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")

    Git().commit("0.0.2", "0.0.3", "v0.0.3")

    assert multiversion_repo.api.head.commit.message == "Update CHANGELOG for 0.0.3\nBump version: 0.0.2 → 0.0.3\n"
    assert git.TagReference(multiversion_repo, path="refs/tags/v0.0.3") in multiversion_repo.api.refs


def test_commit_no_tag(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")

    Git(tag=False).commit("0.0.2", "0.0.3", "v0.0.3")

    assert multiversion_repo.api.head.commit.message == "Update CHANGELOG for 0.0.3\nBump version: 0.0.2 → 0.0.3\n"
    assert git.TagReference(multiversion_repo, path="refs/tags/v0.0.3") not in multiversion_repo.api.refs


def test_commit_reverts_on_tag_failure(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")

    with pytest.raises(errors.VcsError):
        Git().commit("0.0.1", "0.0.2", "0.0.2")

    assert multiversion_repo.api.head.commit.message == "commit log"


@pytest.mark.usefixtures("multiversion_repo")
def test_commit_no_changes():
    with pytest.raises(errors.VcsError) as ex:
        Git().commit("0.0.2", "0.0.3", "v0.0.3")

    assert (
        str(ex.value)
        == """Unable to commit: Cmd('git') failed due to: exit code(1)
  cmdline: git commit --message=Update CHANGELOG for 0.0.3\nBump version: 0.0.2 → 0.0.3
  stdout: 'On branch main
nothing to commit, working tree clean'"""
    )


def test_revert(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log 2")

    assert multiversion_repo.api.head.commit.message == "commit log 2"

    Git().revert()

    assert multiversion_repo.api.head.commit.message == "commit log"


def test_revert_dry_run(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log 2")

    assert multiversion_repo.api.head.commit.message == "commit log 2"

    Git(dry_run=True).revert()

    assert multiversion_repo.api.head.commit.message == "commit log 2"


def test_revert_dulwich(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log 2")

    assert multiversion_repo.api.head.commit.message == "commit log 2"

    Git(provider="dulwich").revert()

    assert multiversion_repo.api.head.commit.message == "commit log"


def test_revert_dry_run_dulwich(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world! v3")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log")

    f.write_text("hello world! v4")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("commit log 2")

    assert multiversion_repo.api.head.commit.message == "commit log 2"

    Git(dry_run=True, provider="dulwich").revert()

    assert multiversion_repo.api.head.commit.message == "commit log 2"
