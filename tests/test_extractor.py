import random
from unittest import mock

import pytest

from changelog_gen import extractor
from changelog_gen.config import Config
from changelog_gen.context import Context
from changelog_gen.extractor import Change, ChangeExtractor
from changelog_gen.vcs import Git


@pytest.fixture()
def multiversion_repo(git_repo):
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


@pytest.fixture()
def conventional_commits(multiversion_repo):
    f = multiversion_repo.workspace / "hello.txt"
    hashes = []
    for msg in [
        """Fix(config): Detail about 4

Refs: #4
""",
        "fix typo",
        """feat(docs)!: Detail about 3

Refs: #3
""",
        """fix: Detail about 1

With some details

BREAKING CHANGE:
Refs: #1
""",
        "update readme",
        """feat: Detail about 2

closes #2
""",
    ]:
        f.write_text(msg)
        multiversion_repo.run("git add hello.txt")
        multiversion_repo.api.index.commit(msg)
        hashes.append(str(multiversion_repo.api.head.commit))
    return hashes


def test_git_commit_extraction(conventional_commits):
    hashes = conventional_commits
    ctx = Context(Config(current_version="0.0.2"))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    sections = e.extract()

    assert sections == {
        "Features and Improvements": {
            "2": Change("2", "Detail about 2", short_hash=hashes[5][:7], commit_hash=hashes[5], commit_type="feat"),
            "3": Change(
                "3",
                "Detail about 3",
                breaking=True,
                scope="(`docs`)",
                short_hash=hashes[2][:7],
                commit_hash=hashes[2],
                commit_type="feat",
            ),
        },
        "Bug fixes": {
            "1": Change(
                "1",
                "Detail about 1",
                breaking=True,
                short_hash=hashes[3][:7],
                commit_hash=hashes[3],
                commit_type="fix",
            ),
            "4": Change(
                "4",
                "Detail about 4",
                scope="(`config`)",
                short_hash=hashes[0][:7],
                commit_hash=hashes[0],
                commit_type="fix",
            ),
        },
    }


def test_git_commit_extraction_include_all(conventional_commits):
    hashes = conventional_commits
    ctx = Context(Config(current_version="0.0.2"))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git, include_all=True)

    sections = e.extract()

    assert sections == {
        "Features and Improvements": {
            "2": Change("2", "Detail about 2", short_hash=hashes[5][:7], commit_hash=hashes[5], commit_type="feat"),
            "3": Change(
                "3",
                "Detail about 3",
                breaking=True,
                scope="(`docs`)",
                short_hash=hashes[2][:7],
                commit_hash=hashes[2],
                commit_type="feat",
            ),
        },
        "Bug fixes": {
            "1": Change(
                "1",
                "Detail about 1",
                breaking=True,
                short_hash=hashes[3][:7],
                commit_hash=hashes[3],
                commit_type="fix",
            ),
            "4": Change(
                "4",
                "Detail about 4",
                scope="(`config`)",
                short_hash=hashes[0][:7],
                commit_hash=hashes[0],
                commit_type="fix",
            ),
        },
        "Miscellaneous": {
            "__1__": Change(
                "__1__",
                "update readme",
                breaking=False,
                short_hash=hashes[4][:7],
                commit_hash=hashes[4],
                commit_type="_misc",
            ),
            "__4__": Change(
                "__4__",
                "fix typo",
                short_hash=hashes[1][:7],
                commit_hash=hashes[1],
                commit_type="_misc",
            ),
        },
    }


def test_git_commit_extraction_handles_random_tags(conventional_commits, multiversion_repo):
    hashes = conventional_commits
    multiversion_repo.api.create_tag("a-random-tag")
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    f.write_text("Detail about 5.")
    multiversion_repo.run("git add hello.txt")
    multiversion_repo.api.index.commit("fix: Detail about 5")
    hashes.append(str(multiversion_repo.api.head.commit))

    ctx = Context(Config(current_version="0.0.2"))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    sections = e.extract()

    assert sections == {
        "Bug fixes": {
            "__0__": Change(
                "__0__",
                "Detail about 5",
                short_hash=hashes[6][:7],
                commit_hash=hashes[6],
                commit_type="fix",
            ),
            "1": Change(
                "1",
                "Detail about 1",
                breaking=True,
                short_hash=hashes[3][:7],
                commit_hash=hashes[3],
                commit_type="fix",
            ),
            "4": Change(
                "4",
                "Detail about 4",
                scope="(`config`)",
                short_hash=hashes[0][:7],
                commit_hash=hashes[0],
                commit_type="fix",
            ),
        },
        "Features and Improvements": {
            "2": Change("2", "Detail about 2", short_hash=hashes[5][:7], commit_hash=hashes[5], commit_type="feat"),
            "3": Change(
                "3",
                "Detail about 3",
                breaking=True,
                scope="(`docs`)",
                short_hash=hashes[2][:7],
                commit_hash=hashes[2],
                commit_type="feat",
            ),
        },
    }


def test_git_commit_extraction_picks_up_custom_types(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    hashes = []
    for msg in [
        """custom: Detail about 1

With some details

BREAKING CHANGE:
Refs: #1
""",
        "update readme",
        """feat: Detail about 2

Refs: #2
""",
    ]:
        f.write_text(msg)
        multiversion_repo.run("git add hello.txt")
        multiversion_repo.api.index.commit(msg)
        hashes.append(str(multiversion_repo.api.head.commit))

    ctx = Context(
        Config(
            commit_types=[
                "custom",
                "feat",
                "bug",
            ],
            type_headers={
                "custom": "Bug fixes",
                "feat": "Features and Improvements",
                "bug": "Bug fixes",
            },
            current_version="0.0.2",
        ),
    )
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    sections = e.extract()

    assert sections == {
        "Features and Improvements": {
            "2": Change("2", "Detail about 2", short_hash=hashes[2][:7], commit_hash=hashes[2], commit_type="feat"),
        },
        "Bug fixes": {
            "1": Change(
                "1",
                "Detail about 1",
                breaking=True,
                short_hash=hashes[0][:7],
                commit_hash=hashes[0],
                commit_type="custom",
            ),
        },
    }


def test_git_commit_extraction_picks_up_additional_allowed_characted(multiversion_repo):
    path = multiversion_repo.workspace
    f = path / "hello.txt"
    hashes = []
    for msg in [
        """fix: Ensure one/two chars? are allowed `and` highlighting, but random PR link ignored. (#20)

With some details

BREAKING CHANGE:
Refs: #1
""",
    ]:
        f.write_text(msg)
        multiversion_repo.run("git add hello.txt")
        multiversion_repo.api.index.commit(msg)
        hashes.append(str(multiversion_repo.api.head.commit))

    ctx = Context(Config(current_version="0.0.2"))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    sections = e.extract()

    assert sections == {
        "Bug fixes": {
            "1": Change(
                "1",
                "Ensure one/two chars? are allowed `and` highlighting, but random PR link ignored.",
                breaking=True,
                short_hash=hashes[0][:7],
                commit_hash=hashes[0],
                commit_type="fix",
                pull_ref="20",
            ),
        },
    }


def test_unique_issues():
    ctx = Context(
        Config(current_version="0.0.0", commit_types=["bug", "feat"]),
    )
    git = mock.Mock()

    e = ChangeExtractor(ctx, git)

    assert e.unique_issues(
        {
            "Unsupported header": {
                "5": Change("5", "Detail about 5", "unsupported"),
            },
            "Feature header": {
                "2": Change("2", "Detail about 2", "feat"),
            },
            "Bug header": {
                "2": Change("2", "Detail about 2", "bug"),
                "3": Change("3", "Detail about 3", "bug"),
                "4": Change("4", "Detail about 4", "bug"),
            },
        },
    ) == ["2", "3", "4"]


@pytest.mark.parametrize(
    ("sections", "commit_types", "minor_regex", "expected_semver"),
    [
        ({"header": {"1": Change("1", "desc", "fix")}}, ["feat"], "feat", "patch"),
        ({"header": {"1": Change("1", "desc", "feat")}}, ["feat"], "feat", "patch"),
        ({"header": {"1": Change("1", "desc", "fix", breaking=True)}}, ["feat"], "feat", "minor"),
        ({"header": {"1": Change("1", "desc", "feat", breaking=True)}}, ["feat"], "feat", "minor"),
        ({"header": {"1": Change("1", "desc", "custom")}}, ["custom"], "feat", "patch"),
        ({"header": {"1": Change("1", "desc", "custom")}}, ["custom"], "feat|custom", "patch"),
        (
            {"header": {"1": Change("1", "desc", "custom", breaking=True)}},
            ["custom"],
            "feat|custom",
            "minor",
        ),
    ],
)
def test_extract_semver_version_zero(sections, commit_types, minor_regex, expected_semver):
    ctx = Context(Config(commit_types=commit_types, current_version="0.0.0", minor_regex=minor_regex))

    semver = extractor.extract_semver(sections, ctx)

    assert semver == expected_semver


@pytest.mark.parametrize(
    ("sections", "commit_types", "minor_regex", "expected_semver"),
    [
        ({"header": {"1": Change("1", "desc", "fix")}}, ["feat"], "feat", "patch"),
        ({"header": {"1": Change("1", "desc", "feat")}}, ["feat"], "feat", "minor"),
        ({"header": {"1": Change("1", "desc", "fix", breaking=True)}}, ["feat"], "feat", "major"),
        ({"header": {"1": Change("1", "desc", "feat", breaking=True)}}, ["feat"], "feat", "major"),
        ({"header": {"1": Change("1", "desc", "custom")}}, ["custom"], "feat", "patch"),
        ({"header": {"1": Change("1", "desc", "custom")}}, ["custom"], "feat|custom", "minor"),
        (
            {"header": {"1": Change("1", "desc", "custom", breaking=True)}},
            ["custom"],
            "feat|custom",
            "major",
        ),
    ],
)
def test_extract_semver(sections, commit_types, minor_regex, expected_semver):
    ctx = Context(Config(commit_types=commit_types, current_version="1.0.0", minor_regex=minor_regex))

    semver = extractor.extract_semver(sections, ctx)

    assert semver == expected_semver


def test_change_ordering():
    changes = [
        Change(
            issue_ref="23",
            description="Small change",
            authors="(edgy, tom)",
            scope="",
            breaking=False,
            commit_type="fix",
        ),
        Change(
            issue_ref="24",
            description="A description",
            authors="(edgy)",
            scope="(writer)",
            breaking=True,
            commit_type="misc",
        ),
        Change(
            issue_ref="25",
            description="Another change",
            authors="(tom)",
            scope="(extractor)",
            breaking=False,
            commit_type="ci",
        ),
        Change(
            issue_ref="26",
            description="Bugfix",
            authors="",
            scope="(extractor)",
            breaking=False,
            commit_type="chore",
        ),
        Change(
            issue_ref="27",
            description="Upgrade python",
            authors="(tom)",
            scope="",
            breaking=True,
            commit_type="custom",
        ),
        Change(
            issue_ref="28",
            description="Update config",
            authors="(edgy)",
            scope="(config)",
            breaking=False,
            commit_type="feat",
        ),
    ]
    random.shuffle(changes)

    assert sorted(changes) == [
        Change(
            issue_ref="24",
            description="A description",
            authors="(edgy)",
            scope="(writer)",
            breaking=True,
            commit_type="misc",
        ),
        Change(
            issue_ref="27",
            description="Upgrade python",
            authors="(tom)",
            scope="",
            breaking=True,
            commit_type="custom",
        ),
        Change(
            issue_ref="28",
            description="Update config",
            authors="(edgy)",
            scope="(config)",
            breaking=False,
            commit_type="feat",
        ),
        Change(
            issue_ref="25",
            description="Another change",
            authors="(tom)",
            scope="(extractor)",
            breaking=False,
            commit_type="ci",
        ),
        Change(
            issue_ref="26",
            description="Bugfix",
            authors="",
            scope="(extractor)",
            breaking=False,
            commit_type="chore",
        ),
        Change(
            issue_ref="23",
            description="Small change",
            authors="(edgy, tom)",
            scope="",
            breaking=False,
            commit_type="fix",
        ),
    ]
