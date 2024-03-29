from unittest import mock

import pytest
import typer
from freezegun import freeze_time

from changelog_gen import errors
from changelog_gen.cli import command
from changelog_gen.config import PostProcessConfig


@pytest.fixture(autouse=True)
def mock_git(monkeypatch):
    mock_git = mock.Mock()
    mock_git.get_current_info.return_value = {
        "dirty": False,
        "branch": "main",
    }
    mock_git.get_logs.return_value = []
    mock_git.find_tag.return_value = "v0.0.0"

    monkeypatch.setattr(command, "Git", mock.Mock(return_value=mock_git))

    return mock_git


@pytest.fixture(autouse=True)
def mock_bump(monkeypatch):
    mock_bump = mock.Mock()
    mock_bump.get_version_info.return_value = {
        "current": "0.0.0",
        "new": "0.0.1",
    }

    monkeypatch.setattr(command, "BumpVersion", mock.Mock(return_value=mock_bump))

    return mock_bump


@pytest.fixture()
def changelog(cwd):
    p = cwd / "CHANGELOG.md"
    p.write_text("# Changelog\n")

    return p


@pytest.fixture()
def _release_notes(cwd):
    r = cwd / "release_notes"
    r.mkdir()
    f = r / ".file"
    f.write_text("")

    for i, note in enumerate(["1.fix", "2.feat", "3.feat", "4.fix"], 1):
        n = r / note
        n.write_text(f"Detail about {i}")


@pytest.fixture()
def commit_factory(mock_git):
    def factory(commits):
        mock_git.get_logs.return_value = [
            (f"short{i}", f"commit-hash{i}", message) for i, message in enumerate(commits)
        ]

    return factory


@pytest.fixture()
def _empty_conventional_commits(): ...


@pytest.fixture()
def _conventional_commits(commit_factory):
    commit_factory(
        [
            """fix: Detail about 4

Refs: #4
""",
            """feat: Detail about 3

Refs: #3
""",
            """feat: Detail about 2

Refs: #2
""",
            """fix: Detail about 1

With some details

Refs: #1
""",
        ],
    )


@pytest.fixture()
def _breaking_conventional_commits(commit_factory):
    commit_factory(
        [
            """fix: Detail about 4

Refs: #4
""",
            """feat: Detail about 3

Refs: #3
""",
            """feat!: Detail about 2

Refs: #2
""",
            """fix: Detail about 1

With some details

Refs: #1
""",
        ],
    )


@pytest.fixture()
def post_process_pyproject(cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
commit = true
post_process.url = "https://my-api/::issue_ref::/release"
post_process.auth_env = "MY_API_AUTH"
""",
    )

    return p


@pytest.mark.usefixtures("changelog")
def test_generate_wraps_changelog_errors(gen_cli_runner, monkeypatch):
    monkeypatch.setattr(command, "_gen", mock.Mock(side_effect=errors.ChangelogException("Unable to parse.")))
    result = gen_cli_runner.invoke()

    assert result.exit_code == 1
    assert result.output.strip() == "Unable to parse."


@pytest.mark.usefixtures("cwd")
def test_generate_aborts_if_changelog_missing(gen_cli_runner):
    result = gen_cli_runner.invoke()

    assert result.exit_code == 1
    assert result.output.strip() == "No CHANGELOG file detected, run `changelog init`"


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_aborts_if_dirty(gen_cli_runner, cwd, mock_git):
    mock_git.get_current_info.return_value = {
        "dirty": True,
        "branch": "main",
    }
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = false
""",
    )
    result = gen_cli_runner.invoke()

    assert result.exit_code == 1
    assert result.output.strip() == "Working directory is not clean. Use `allow_dirty` configuration to ignore."


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_allows_dirty(gen_cli_runner, cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = false
""",
    )
    result = gen_cli_runner.invoke(["--allow-dirty"])

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_continues_if_allow_dirty_configured(gen_cli_runner, cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = true
""",
    )
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_aborts_if_unsupported_current_branch(gen_cli_runner, cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = true
allowed_branches = ["release_candidate"]
""",
    )
    result = gen_cli_runner.invoke()

    assert result.exit_code == 1
    assert result.output.strip() == "Current branch not in allowed generation branches."


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_allows_supported_branch(gen_cli_runner, cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = true
allowed_branches = ["main"]
""",
    )
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_confirms_suggested_changes(gen_cli_runner):
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0
    assert (
        "\n".join([f"{r.rstrip(' ')}" for r in result.output.split("\n")])
        == """

## v0.0.1

### Features and Improvements

- Detail about 2 [#2]
- Detail about 3 [#3]

### Bug fixes

- Detail about 1 [#1]
- Detail about 4 [#4]



Write CHANGELOG for suggested version 0.0.1 [y/N]:
"""
    )


@pytest.mark.usefixtures("changelog", "_conventional_commits")
@pytest.mark.backwards_compat()
def test_generate_with_section_mapping_backwards_compat(gen_cli_runner, cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = true
section_mapping.feat = "fix"
""",
    )
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0
    assert (
        "\n".join([f"{r.rstrip(' ')}" for r in result.output.split("\n")])
        == """

## v0.0.1

### Bug fixes

- Detail about 1 [#1]
- Detail about 2 [#2]
- Detail about 3 [#3]
- Detail about 4 [#4]



Write CHANGELOG for suggested version 0.0.1 [y/N]:
"""
    )


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_with_headers(gen_cli_runner, cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
allow_dirty = true
commit_types.feat.header = "My Features"
commit_types.fix.header = "My Fixes"
""",
    )
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0
    assert (
        "\n".join([f"{r.rstrip(' ')}" for r in result.output.split("\n")])
        == """

## v0.0.1

### My Features

- Detail about 2 [#2]
- Detail about 3 [#3]

### My Fixes

- Detail about 1 [#1]
- Detail about 4 [#4]



Write CHANGELOG for suggested version 0.0.1 [y/N]:
"""
    )


@pytest.mark.usefixtures("_conventional_commits")
def test_generate_writes_to_file(
    gen_cli_runner,
    changelog,
    monkeypatch,
):
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0

    assert (
        changelog.read_text()
        == """
# Changelog

## v0.0.1

### Features and Improvements

- Detail about 2 [#2]
- Detail about 3 [#3]

### Bug fixes

- Detail about 1 [#1]
- Detail about 4 [#4]
""".lstrip()
    )


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_creates_release(
    gen_cli_runner,
    monkeypatch,
    mock_git,
    mock_bump,
):
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke(["--commit", "--release"])

    assert result.exit_code == 0
    assert mock_git.commit.call_args == mock.call("0.0.1", ["CHANGELOG.md"])
    assert mock_bump.release.call_args == mock.call("0.0.1")


@pytest.mark.backwards_compat()
@pytest.mark.usefixtures("changelog", "_release_notes")
def test_generate_creates_release_from_notes(
    gen_cli_runner,
    monkeypatch,
    mock_git,
    mock_bump,
):
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke(["--commit", "--release"])

    assert result.exit_code == 0

    assert mock_git.commit.call_args == mock.call("0.0.1", ["CHANGELOG.md", "release_notes"])
    assert mock_bump.release.call_args == mock.call("0.0.1")


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_creates_release_using_config(
    gen_cli_runner,
    cwd,
    monkeypatch,
    mock_git,
    mock_bump,
):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
commit = true
release = true
""",
    )

    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0
    assert mock_git.commit.call_args == mock.call("0.0.1", ["CHANGELOG.md"])
    assert mock_bump.release.call_args == mock.call("0.0.1")


@pytest.mark.usefixtures("changelog")
def test_generate_creates_release_without_release_notes(
    gen_cli_runner,
    cwd,
    commit_factory,
    monkeypatch,
):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
commit = true
release = true
""",
    )

    commit_factory(
        [
            """feat: Detail about 2

Refs: #2
""",
            "update readme",
            """fix: Detail about 1

With some details

BREAKING CHANGE:
Refs: #1
""",
            """feat(docs)!: Detail about 3

Refs: #3
""",
            "fix typo",
            """fix(config): Detail about 4

Refs: #4
""",
        ],
    )

    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke()

    assert result.exit_code == 0


@pytest.mark.usefixtures("changelog", "_conventional_commits")
def test_generate_handles_bumpversion_failure_and_reverts_changelog_commit(
    gen_cli_runner,
    cwd,
    monkeypatch,
    mock_git,
    mock_bump,
):
    p = cwd / "pyproject.toml"
    p.write_text(
        """
[tool.changelog_gen]
commit = true
release = true
""",
    )

    mock_bump.release.side_effect = Exception
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))

    result = gen_cli_runner.invoke()

    assert result.exit_code == 1
    assert mock_git.commit.call_args == mock.call("0.0.1", ["CHANGELOG.md"])
    assert mock_bump.release.call_args == mock.call("0.0.1")
    assert mock_git.revert.call_args == mock.call()


@pytest.mark.usefixtures("_conventional_commits")
def test_generate_uses_supplied_version_tag(
    gen_cli_runner,
    changelog,
    monkeypatch,
    mock_git,
):
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke(["--version-tag", "0.3.2", "--commit"])

    assert result.exit_code == 0
    assert (
        changelog.read_text()
        == """
# Changelog

## v0.3.2

### Features and Improvements

- Detail about 2 [#2]
- Detail about 3 [#3]

### Bug fixes

- Detail about 1 [#1]
- Detail about 4 [#4]
""".lstrip()
    )
    assert mock_git.commit.call_args == mock.call("0.3.2", ["CHANGELOG.md"])


@pytest.mark.usefixtures("_conventional_commits", "changelog")
def test_generate_uses_supplied_version_part(
    gen_cli_runner,
    monkeypatch,
    mock_bump,
):
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke(["--version-part", "major", "--commit"])

    assert result.exit_code == 0
    assert mock_bump.get_version_info.call_args == mock.call("major")


@pytest.mark.usefixtures("_conventional_commits")
def test_generate_dry_run(
    gen_cli_runner,
    changelog,
    monkeypatch,
):
    monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
    result = gen_cli_runner.invoke(["--dry-run"])

    assert result.exit_code == 0

    assert (
        changelog.read_text()
        == """
# Changelog
""".lstrip()
    )


@pytest.mark.usefixtures("_empty_conventional_commits")
def test_generate_reject_empty(
    gen_cli_runner,
    changelog,
):
    result = gen_cli_runner.invoke(["--reject-empty"])

    assert result.exit_code == 0
    assert result.output.strip() == "No changes present and reject_empty configured."

    assert (
        changelog.read_text()
        == """
# Changelog
""".lstrip()
    )


class TestDelegatesToPerIssuePostProcess:
    # The behaviour of per_issue_post_process are tested in test_post_processor

    @pytest.mark.usefixtures("_conventional_commits", "changelog", "post_process_pyproject")
    def test_load_config(
        self,
        gen_cli_runner,
        monkeypatch,
    ):
        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        post_process_mock = mock.MagicMock()
        monkeypatch.setattr(command, "per_issue_post_process", post_process_mock)

        result = gen_cli_runner.invoke()

        assert result.exit_code == 0
        assert post_process_mock.call_args_list == [
            mock.call(
                PostProcessConfig(
                    url="https://my-api/::issue_ref::/release",
                    auth_env="MY_API_AUTH",
                ),
                ["1", "2", "3", "4"],
                "0.0.1",
                dry_run=False,
            ),
        ]

    @pytest.mark.usefixtures("_conventional_commits", "changelog", "post_process_pyproject")
    def test_generate_post_process_url(
        self,
        gen_cli_runner,
        monkeypatch,
    ):
        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        post_process_mock = mock.MagicMock()
        monkeypatch.setattr(command, "per_issue_post_process", post_process_mock)

        api_url = "https://my-api/::issue_ref::/comment"
        result = gen_cli_runner.invoke(["--post-process-url", api_url])

        assert result.exit_code == 0
        assert post_process_mock.call_args_list == [
            mock.call(
                PostProcessConfig(
                    url=api_url,
                    auth_env="MY_API_AUTH",
                ),
                ["1", "2", "3", "4"],
                "0.0.1",
                dry_run=False,
            ),
        ]

    @pytest.mark.usefixtures("_conventional_commits", "changelog", "post_process_pyproject")
    def test_generate_post_process_auth_env(
        self,
        gen_cli_runner,
        monkeypatch,
    ):
        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        post_process_mock = mock.MagicMock()
        monkeypatch.setattr(command, "per_issue_post_process", post_process_mock)

        result = gen_cli_runner.invoke(["--post-process-auth-env", "OTHER_API_AUTH"])

        assert result.exit_code == 0
        assert post_process_mock.call_args_list == [
            mock.call(
                PostProcessConfig(
                    url="https://my-api/::issue_ref::/release",
                    auth_env="OTHER_API_AUTH",
                ),
                ["1", "2", "3", "4"],
                "0.0.1",
                dry_run=False,
            ),
        ]

    @pytest.mark.usefixtures("_conventional_commits", "changelog", "post_process_pyproject")
    def test_generate_dry_run(
        self,
        gen_cli_runner,
        monkeypatch,
    ):
        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        post_process_mock = mock.MagicMock()
        monkeypatch.setattr(command, "per_issue_post_process", post_process_mock)

        result = gen_cli_runner.invoke(["--dry-run"])

        assert result.exit_code == 0
        assert post_process_mock.call_args_list == [
            mock.call(
                PostProcessConfig(
                    url="https://my-api/::issue_ref::/release",
                    auth_env="MY_API_AUTH",
                ),
                ["1", "2", "3", "4"],
                "0.0.1",
                dry_run=True,
            ),
        ]

    @pytest.mark.usefixtures("_conventional_commits", "changelog", "post_process_pyproject")
    def test_generate_decline_changes(
        self,
        gen_cli_runner,
        monkeypatch,
    ):
        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=False))
        post_process_mock = mock.MagicMock()
        monkeypatch.setattr(command, "per_issue_post_process", post_process_mock)

        result = gen_cli_runner.invoke([])

        assert result.exit_code == 0
        assert post_process_mock.call_count == 0


@freeze_time("2022-04-14T16:45:03")
class TestGenerateWithDate:
    @pytest.mark.usefixtures("_conventional_commits", "changelog")
    def test_using_config(self, gen_cli_runner, cwd, monkeypatch):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.changelog_gen]
commit = false
release = true
date_format = "on %Y-%m-%d"
        """.strip(),
        )

        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        writer_mock = mock.MagicMock()
        monkeypatch.setattr(command.writer, "new_writer", mock.MagicMock(return_value=writer_mock))

        r = gen_cli_runner.invoke()

        assert r.exit_code == 0, r.output
        assert writer_mock.add_version.call_args == mock.call("v0.0.1 on 2022-04-14")

    @pytest.mark.usefixtures("_conventional_commits", "changelog")
    def test_using_cli(self, gen_cli_runner, monkeypatch):
        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        writer_mock = mock.MagicMock()
        monkeypatch.setattr(command.writer, "new_writer", mock.MagicMock(return_value=writer_mock))

        r = gen_cli_runner.invoke(["--date-format", "(%Y-%m-%d at %H:%M)"])

        assert r.exit_code == 0, r.output
        assert writer_mock.add_version.call_args == mock.call("v0.0.1 (2022-04-14 at 16:45)")

    @pytest.mark.usefixtures("_conventional_commits", "changelog")
    def test_override_config(self, gen_cli_runner, cwd, monkeypatch):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.changelog_gen]
commit = false
release = true
date_format = "on %Y-%m-%d"
        """.strip(),
        )

        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        writer_mock = mock.MagicMock()
        monkeypatch.setattr(command.writer, "new_writer", mock.MagicMock(return_value=writer_mock))

        r = gen_cli_runner.invoke(["--date-format", "(%Y-%m-%d at %H:%M)"])

        assert r.exit_code == 0, r.output
        assert writer_mock.add_version.call_args == mock.call("v0.0.1 (2022-04-14 at 16:45)")

    @pytest.mark.usefixtures("_conventional_commits", "changelog")
    def test_override_config_and_disable(self, gen_cli_runner, cwd, monkeypatch):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.changelog_gen]
commit = false
release = true
date_format = "on %Y-%m-%d"
        """.strip(),
        )

        monkeypatch.setattr(typer, "confirm", mock.MagicMock(return_value=True))
        writer_mock = mock.MagicMock()
        monkeypatch.setattr(command.writer, "new_writer", mock.MagicMock(return_value=writer_mock))

        r = gen_cli_runner.invoke(["--date-format", ""])

        assert r.exit_code == 0, r.output
        assert writer_mock.add_version.call_args == mock.call("v0.0.1")
