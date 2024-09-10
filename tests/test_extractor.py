import random

import pytest

from changelog_gen import extractor
from changelog_gen.config import Config, GithubConfig
from changelog_gen.context import Context
from changelog_gen.extractor import Change, ChangeExtractor, Footer, Link
from changelog_gen.vcs import Git


@pytest.fixture
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


@pytest.fixture
def conventional_commits(multiversion_repo):
    f = multiversion_repo.workspace / "hello.txt"
    hashes = []
    for msg in [
        """Fix(config): Detail about 4

Refs: #4
""",
        "fix typo",
        """feat(docs)!: Detail about 3

Fixes #3
""",
        """fix: Detail about 1

With some details

BREAKING CHANGE:
Refs: #1
""",
        "update readme",
        """feat: Detail about 2 (#2)

Authors: @tom, @edgy
closes #2
""",
    ]:
        f.write_text(msg)
        multiversion_repo.run("git add hello.txt")
        multiversion_repo.api.index.commit(msg)
        hashes.append(str(multiversion_repo.api.head.commit))
    return hashes


def test_change_with_issue_ref():
    change = Change(
        "Features and Improvements",
        "Detail about 2",
        short_hash="short-hash",
        commit_hash="commit-hash",
        commit_type="feat",
        footers=[
            Footer("Refs", ": ", "#2"),
        ],
    )

    assert change.issue_ref == "#2"


def test_change_without_issue_ref():
    change = Change(
        "Features and Improvements",
        "Detail about 2",
        short_hash="short-hash",
        commit_hash="commit-hash",
        commit_type="feat",
        footers=[
            Footer("Authors", ": ", "(edgy)"),
        ],
    )

    assert change.issue_ref == ""


def test_git_commit_extraction(conventional_commits):
    hashes = conventional_commits
    ctx = Context(Config(current_version="0.0.2"))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    changes = e.extract()

    assert changes == [
        Change(
            "Features and Improvements",
            "Detail about 2 (#2)",
            short_hash=hashes[5][:7],
            commit_hash=hashes[5],
            commit_type="feat",
            footers=[
                Footer("Authors", ": ", "@tom, @edgy"),
            ],
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[3][:7],
            commit_hash=hashes[3],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
        ),
        Change(
            "Features and Improvements",
            "Detail about 3",
            breaking=True,
            scope="docs",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
            footers=[],
        ),
        Change(
            "Bug fixes",
            "Detail about 4",
            scope="config",
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#4"),
            ],
        ),
    ]


def test_git_commit_extraction_include_all(conventional_commits):
    hashes = conventional_commits
    ctx = Context(Config(current_version="0.0.2"))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git, include_all=True)

    changes = e.extract()

    assert changes == [
        Change(
            "Features and Improvements",
            "Detail about 2 (#2)",
            short_hash=hashes[5][:7],
            commit_hash=hashes[5],
            commit_type="feat",
            footers=[
                Footer("Authors", ": ", "@tom, @edgy"),
            ],
        ),
        Change(
            "Miscellaneous",
            "update readme",
            breaking=False,
            short_hash=hashes[4][:7],
            commit_hash=hashes[4],
            commit_type="_misc",
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[3][:7],
            commit_hash=hashes[3],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
        ),
        Change(
            "Features and Improvements",
            "Detail about 3",
            breaking=True,
            scope="docs",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
            footers=[],
        ),
        Change(
            "Miscellaneous",
            "fix typo",
            short_hash=hashes[1][:7],
            commit_hash=hashes[1],
            commit_type="_misc",
        ),
        Change(
            "Bug fixes",
            "Detail about 4",
            scope="config",
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#4"),
            ],
        ),
    ]


def test_git_commit_extraction_extractors(conventional_commits):
    hashes = conventional_commits
    extractors = [
        {"footer": ["Refs", "fixes"], "pattern": r"#(?P<issue_ref>\d+)"},
        {"footer": "Authors", "pattern": r"@(?P<author>\w+)"},
    ]
    ctx = Context(Config(current_version="0.0.2", extractors=extractors))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    changes = e.extract()

    assert changes == [
        Change(
            "Features and Improvements",
            "Detail about 2 (#2)",
            short_hash=hashes[5][:7],
            commit_hash=hashes[5],
            commit_type="feat",
            footers=[
                Footer("Authors", ": ", "@tom, @edgy"),
            ],
            extractions={"author": ["tom", "edgy"]},
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[3][:7],
            commit_hash=hashes[3],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
            extractions={"issue_ref": ["1"]},
        ),
        Change(
            "Features and Improvements",
            "Detail about 3",
            breaking=True,
            scope="docs",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
        ),
        Change(
            "Bug fixes",
            "Detail about 4",
            scope="config",
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#4"),
            ],
            extractions={"issue_ref": ["4"]},
        ),
    ]


def test_git_commit_extraction_link_generators(conventional_commits):
    hashes = conventional_commits
    extractors = [
        {"footer": "Refs", "pattern": r"#(?P<issue_ref>\d+)"},
        {"footer": "fixes", "pattern": r"#(?P<issue_ref>\d+)"},
        {"footer": "Authors", "pattern": r"@(?P<author>\w+)"},
    ]
    link_generators = [
        {"source": "issue_ref", "link": "https://github.com/NRWLDev/changelog-gen/issues/{0}"},
        {"source": "author", "link": "https://github.com/{0}", "text": "@{0}"},
        {
            "source": "__change__",
            "link": "https://github.com/NRWLDev/changelog-gen/commit/{0.commit_hash}",
            "text": "{0.short_hash}",
        },
    ]
    ctx = Context(Config(current_version="0.0.2", link_generators=link_generators, extractors=extractors))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    changes = e.extract()

    assert changes == [
        Change(
            "Features and Improvements",
            "Detail about 2 (#2)",
            short_hash=hashes[5][:7],
            commit_hash=hashes[5],
            commit_type="feat",
            footers=[
                Footer("Authors", ": ", "@tom, @edgy"),
            ],
            links=[
                Link("@tom", "https://github.com/tom"),
                Link("@edgy", "https://github.com/edgy"),
                Link(hashes[5][:7], f"https://github.com/NRWLDev/changelog-gen/commit/{hashes[5]}"),
            ],
            extractions={"author": ["tom", "edgy"]},
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[3][:7],
            commit_hash=hashes[3],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
            links=[
                Link("1", "https://github.com/NRWLDev/changelog-gen/issues/1"),
                Link(hashes[3][:7], f"https://github.com/NRWLDev/changelog-gen/commit/{hashes[3]}"),
            ],
            extractions={"issue_ref": ["1"]},
        ),
        Change(
            "Features and Improvements",
            "Detail about 3",
            breaking=True,
            scope="docs",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
            links=[
                Link(hashes[2][:7], f"https://github.com/NRWLDev/changelog-gen/commit/{hashes[2]}"),
            ],
        ),
        Change(
            "Bug fixes",
            "Detail about 4",
            scope="config",
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#4"),
            ],
            links=[
                Link("4", "https://github.com/NRWLDev/changelog-gen/issues/4"),
                Link(hashes[0][:7], f"https://github.com/NRWLDev/changelog-gen/commit/{hashes[0]}"),
            ],
            extractions={"issue_ref": ["4"]},
        ),
    ]


def test_git_commit_extraction_with_github_optionals(conventional_commits):
    hashes = conventional_commits
    extractors = [
        {"footer": ["Refs", "fixes"], "pattern": r"#(?P<issue_ref>\d+)"},
        {"footer": "Authors", "pattern": r"@(?P<author>\w+)"},
    ]
    ctx = Context(
        Config(
            current_version="0.0.2",
            extractors=extractors,
            github=GithubConfig(
                strip_pr_from_description=True,
                extract_pr_from_description=True,
                extract_common_footers=True,
            ),
        ),
    )
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    changes = e.extract()

    assert changes == [
        Change(
            "Features and Improvements",
            "Detail about 2",
            short_hash=hashes[5][:7],
            commit_hash=hashes[5],
            commit_type="feat",
            footers=[
                Footer("PR", ": ", "#2"),
                Footer("Authors", ": ", "@tom, @edgy"),
                Footer("closes", " ", "#2"),
            ],
            extractions={"author": ["tom", "edgy"]},
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[3][:7],
            commit_hash=hashes[3],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
            extractions={"issue_ref": ["1"]},
        ),
        Change(
            "Features and Improvements",
            "Detail about 3",
            breaking=True,
            scope="docs",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
            footers=[
                Footer("Fixes", " ", "#3"),
            ],
            extractions={"issue_ref": ["3"]},
        ),
        Change(
            "Bug fixes",
            "Detail about 4",
            scope="config",
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#4"),
            ],
            extractions={"issue_ref": ["4"]},
        ),
    ]


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

    changes = e.extract()

    assert changes == [
        Change(
            "Bug fixes",
            "Detail about 5",
            short_hash=hashes[6][:7],
            commit_hash=hashes[6],
            commit_type="fix",
        ),
        Change(
            "Features and Improvements",
            "Detail about 2 (#2)",
            short_hash=hashes[5][:7],
            commit_hash=hashes[5],
            commit_type="feat",
            footers=[
                Footer("Authors", ": ", "@tom, @edgy"),
            ],
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[3][:7],
            commit_hash=hashes[3],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
        ),
        Change(
            "Features and Improvements",
            "Detail about 3",
            breaking=True,
            scope="docs",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
            footers=[],
        ),
        Change(
            "Bug fixes",
            "Detail about 4",
            scope="config",
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#4"),
            ],
        ),
    ]


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

    changes = e.extract()

    assert changes == [
        Change(
            "Features and Improvements",
            "Detail about 2",
            short_hash=hashes[2][:7],
            commit_hash=hashes[2],
            commit_type="feat",
            footers=[
                Footer("Refs", ": ", "#2"),
            ],
        ),
        Change(
            "Bug fixes",
            "Detail about 1",
            breaking=True,
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="custom",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
        ),
    ]


def test_git_commit_extraction_picks_up_additional_allowed_character(multiversion_repo):
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

    ctx = Context(Config(current_version="0.0.2", github=GithubConfig(strip_pr_from_description=True)))
    git = Git(ctx)

    e = ChangeExtractor(ctx, git)

    changes = e.extract()

    assert changes == [
        Change(
            "Bug fixes",
            "Ensure one/two chars? are allowed `and` highlighting, but random PR link ignored.",
            breaking=True,
            short_hash=hashes[0][:7],
            commit_hash=hashes[0],
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#1"),
            ],
        ),
    ]


@pytest.mark.parametrize(
    ("changes", "commit_types", "minor_regex", "expected_semver"),
    [
        ([Change("header", "desc", "fix")], ["feat"], "feat", "patch"),
        ([Change("header", "desc", "feat")], ["feat"], "feat", "patch"),
        ([Change("header", "desc", "fix", breaking=True)], ["feat"], "feat", "minor"),
        ([Change("header", "desc", "feat", breaking=True)], ["feat"], "feat", "minor"),
        ([Change("header", "desc", "custom")], ["custom"], "feat", "patch"),
        ([Change("header", "desc", "custom")], ["custom"], "feat|custom", "patch"),
        (
            [Change("header", "desc", "custom", breaking=True)],
            ["custom"],
            "feat|custom",
            "minor",
        ),
    ],
)
def test_extract_semver_version_zero(changes, commit_types, minor_regex, expected_semver):
    ctx = Context(Config(commit_types=commit_types, current_version="0.0.0", minor_regex=minor_regex))

    semver = extractor.extract_semver(changes, ctx)

    assert semver == expected_semver


@pytest.mark.parametrize(
    ("changes", "commit_types", "minor_regex", "expected_semver"),
    [
        ([Change("header", "desc", "fix")], ["feat"], "feat", "patch"),
        ([Change("header", "desc", "feat")], ["feat"], "feat", "minor"),
        ([Change("header", "desc", "fix", breaking=True)], ["feat"], "feat", "major"),
        ([Change("header", "desc", "feat", breaking=True)], ["feat"], "feat", "major"),
        ([Change("header", "desc", "custom")], ["custom"], "feat", "patch"),
        ([Change("header", "desc", "custom")], ["custom"], "feat|custom", "minor"),
        (
            [Change("header", "desc", "custom", breaking=True)],
            ["custom"],
            "feat|custom",
            "major",
        ),
    ],
)
def test_extract_semver(changes, commit_types, minor_regex, expected_semver):
    ctx = Context(Config(commit_types=commit_types, current_version="1.0.0", minor_regex=minor_regex))

    semver = extractor.extract_semver(changes, ctx)

    assert semver == expected_semver


def test_change_ordering():
    changes = [
        Change(
            header="header",
            description="Small change",
            scope="",
            breaking=False,
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#23"),
                Footer("Authors", ": ", "(edgy, tom)"),
            ],
        ),
        Change(
            header="header",
            description="A description",
            scope="(writer)",
            breaking=True,
            commit_type="misc",
            footers=[
                Footer("Refs", ": ", "#24"),
                Footer("Authors", ": ", "(edgy)"),
            ],
        ),
        Change(
            header="header",
            description="Another change",
            scope="(extractor)",
            breaking=False,
            commit_type="ci",
            footers=[
                Footer("Refs", ": ", "#25"),
                Footer("Authors", ": ", "(tom)"),
            ],
        ),
        Change(
            header="header",
            description="Bugfix",
            scope="(extractor)",
            breaking=False,
            commit_type="chore",
            footers=[
                Footer("Refs", ": ", "#26"),
            ],
        ),
        Change(
            header="header",
            description="Upgrade python",
            scope="",
            breaking=True,
            commit_type="custom",
            footers=[
                Footer("Refs", ": ", "#27"),
                Footer("Authors", ": ", "(tom)"),
            ],
        ),
        Change(
            header="header",
            description="Update config",
            scope="(config)",
            breaking=False,
            commit_type="feat",
            footers=[
                Footer("Refs", ": ", "#28"),
                Footer("Authors", ": ", "(edgy)"),
            ],
        ),
    ]
    random.shuffle(changes)

    assert sorted(changes) == [
        Change(
            header="header",
            description="A description",
            scope="(writer)",
            breaking=True,
            commit_type="misc",
            footers=[
                Footer("Refs", ": ", "#24"),
                Footer("Authors", ": ", "(edgy)"),
            ],
        ),
        Change(
            header="header",
            description="Upgrade python",
            scope="",
            breaking=True,
            commit_type="custom",
            footers=[
                Footer("Refs", ": ", "#27"),
                Footer("Authors", ": ", "(tom)"),
            ],
        ),
        Change(
            header="header",
            description="Update config",
            scope="(config)",
            breaking=False,
            commit_type="feat",
            footers=[
                Footer("Refs", ": ", "#28"),
                Footer("Authors", ": ", "(edgy)"),
            ],
        ),
        Change(
            header="header",
            description="Another change",
            scope="(extractor)",
            breaking=False,
            commit_type="ci",
            footers=[
                Footer("Refs", ": ", "#25"),
                Footer("Authors", ": ", "(tom)"),
            ],
        ),
        Change(
            header="header",
            description="Bugfix",
            scope="(extractor)",
            breaking=False,
            commit_type="chore",
            footers=[
                Footer("Refs", ": ", "#26"),
            ],
        ),
        Change(
            header="header",
            description="Small change",
            scope="",
            breaking=False,
            commit_type="fix",
            footers=[
                Footer("Refs", ": ", "#23"),
                Footer("Authors", ": ", "(edgy, tom)"),
            ],
        ),
    ]
