import re

import pytest

from changelog_gen import config, errors


@pytest.fixture()
def config_factory(cwd):
    def factory(contents=None):
        p = cwd / "pyproject.toml"
        p.touch()
        if contents:
            p.write_text(contents)

    return factory


@pytest.fixture()
def pyproject_factory(cwd):
    def factory(contents=None):
        p = cwd / "pyproject.toml"
        p.touch()
        if contents:
            p.write_text(contents)

    return factory


@pytest.fixture()
def _empty_config(config_factory):
    config_factory()


def test_read_handles_missing_file(cwd):
    p = cwd / "pyproject.toml"
    p.unlink()
    assert config.read() == config.Config()


@pytest.mark.usefixtures("_empty_config")
def test_read_handles_empty_file():
    assert config.read() == config.Config()


class TestPyprojectToml:
    @pytest.mark.parametrize(
        ("value", "exp_key", "exp_value"),
        [
            ("release = true", "release", True),
            ("commit = true", "commit", True),
            ("allow_dirty = true", "allow_dirty", True),
            ("allow_missing = true", "allow_missing", True),
            ("reject_empty = true", "reject_empty", True),
            ("release = false", "release", False),
            ("commit = false", "commit", False),
            ("allow_dirty = false", "allow_dirty", False),
            ("allow_missing = false", "allow_missing", False),
            ("reject_empty = false", "reject_empty", False),
        ],
    )
    def test_read_picks_up_boolean_values(self, config_factory, value, exp_key, exp_value):
        config_factory(
            f"""
[tool.changelog_gen]
{value}
""",
        )

        c = config.read()
        assert getattr(c, exp_key) == exp_value

    def test_read_picks_up_strings_values(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
issue_link = "https://github.com/NRWLDev/changelog-gen/issues/::issue_ref::"
""",
        )

        c = config.read()
        assert c.issue_link == "https://github.com/NRWLDev/changelog-gen/issues/::issue_ref::"

    def test_read_picks_up_list_values(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
allowed_branches = [
    "main",
    "feature/11",
]
""",
        )

        c = config.read()
        assert c.allowed_branches == ["main", "feature/11"]

    def test_read_picks_up_commit_types(self, config_factory):
        config_factory(
            """
[tool.changelog_gen.commit_types]
bug.header = "Bug fixes"
docs.header = "Documentation"
feat.header = "Features and Improvements"
feat.semver = "minor"
feature.header = "Features and Improvements"
feature.semver = "minor"
fix.header = "Bug fixes"
misc.header = "Miscellaneous"
test.header = "Bug fixes"
""",
        )

        c = config.read()
        assert c.commit_types == {
            "bug": config.CommitType(
                header="Bug fixes",
            ),
            "chore": config.CommitType(header="Miscellaneous", semver="patch"),
            "ci": config.CommitType(header="Miscellaneous", semver="patch"),
            "docs": config.CommitType(
                header="Documentation",
            ),
            "feat": config.CommitType(
                header="Features and Improvements",
                semver="minor",
            ),
            "feature": config.CommitType(
                header="Features and Improvements",
                semver="minor",
            ),
            "fix": config.CommitType(
                header="Bug fixes",
            ),
            "misc": config.CommitType(
                header="Miscellaneous",
            ),
            "perf": config.CommitType(header="Miscellaneous", semver="patch"),
            "refactor": config.CommitType(header="Miscellaneous", semver="patch"),
            "revert": config.CommitType(header="Miscellaneous", semver="patch"),
            "style": config.CommitType(header="Miscellaneous", semver="patch"),
            "test": config.CommitType(
                header="Bug fixes",
            ),
        }


class TestPostProcessConfig:
    def test_read_picks_up_no_post_process_config(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
release = true
        """,
        )

        c = config.read()
        assert c.post_process is None

    def test_read_picks_up_issue_link(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
issue_link = "https://fake_rest_api/::issue_ref::"
""",
        )

        c = config.read()
        assert c.issue_link == "https://fake_rest_api/::issue_ref::"

    def test_read_picks_up_commit_link(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
commit_link = "https://fake_rest_api/::commit_hash::"
""",
        )

        c = config.read()
        assert c.commit_link == "https://fake_rest_api/::commit_hash::"

    def test_read_picks_up_post_process_config_pyproject(self, config_factory):
        config_factory(
            """
[tool.changelog_gen.post_process]
url = "https://fake_rest_api/::commit_hash::"
verb = "PUT"
body = '{"issue": "::issue_ref::", "comment": "Released in ::version::"}'
auth_env = "MY_API_AUTH"
headers."content-type" = "application/json"
""",
        )

        c = config.read()
        assert c.post_process == config.PostProcessConfig(
            url="https://fake_rest_api/::commit_hash::",
            verb="PUT",
            body='{"issue": "::issue_ref::", "comment": "Released in ::version::"}',
            auth_env="MY_API_AUTH",
            headers={"content-type": "application/json"},
        )

    @pytest.mark.parametrize(
        "config_value",
        [
            'issue_link = "::unexpected:: ::also-unexpected::"',
            'commit_link = "::unexpected:: ::also-unexpected::"',
            'post_process.body = "::unexpected:: ::also-unexpected::"',
            'post_process.url = "::unexpected:: ::also-unexpected::"',
        ],
    )
    def test_read_picks_up_unexpected_replaces(self, config_factory, config_value):
        config_factory(
            f"""
[tool.changelog_gen]
{config_value}
        """,
        )

        with pytest.raises(errors.UnsupportedReplaceError) as e:
            config.read()

        assert str(e.value) == "Replace string(s) ('::also-unexpected::', '::unexpected::') not supported."

    def test_read_picks_up_post_process_override(self, config_factory):
        config_factory(
            """
[tool.changelog_gen.post_process]
url = "https://initial/::issue_ref::"
auth_env = "INITIAL"
""",
        )

        c = config.read(
            post_process_url="https://fake_rest_api/",
            post_process_auth_env="MY_API_AUTH",
        )
        assert c.post_process == config.PostProcessConfig(
            url="https://fake_rest_api/",
            auth_env="MY_API_AUTH",
        )

    def test_read_picks_up_post_process_override_no_config(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
release = true
""",
        )

        c = config.read(
            post_process_url="https://fake_rest_api/",
            post_process_auth_env="MY_API_AUTH",
        )
        assert c.post_process == config.PostProcessConfig(
            url="https://fake_rest_api/",
            auth_env="MY_API_AUTH",
        )

    @pytest.mark.parametrize(("url", "auth_env"), [("", "AUTH"), ("url", "")])
    def test_read_ignores_empty_post_process_override(self, config_factory, url, auth_env):
        config_factory(
            """
[tool.changelog_gen.post_process]
url = "https://initial/::issue_ref::"
auth_env = "INITIAL"
""",
        )

        c = config.read(
            post_process_url=url,
            post_process_auth_env=auth_env,
        )
        assert c.post_process == config.PostProcessConfig(
            url=url or "https://initial/::issue_ref::",
            auth_env=auth_env or "INITIAL",
        )

    def test_read_rejects_unknown_fields(self, config_factory):
        config_factory(
            """
[tool.changelog_gen.post_process]
enabled = false
""",
        )
        with pytest.raises(RuntimeError, match="^Failed to create post_process: .*"):
            config.read()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("release", True),
        ("commit", True),
        ("allow_dirty", True),
        ("reject_empty", True),
        ("date_format", "%Y-%m-%d"),
    ],
)
def test_read_overrides(config_factory, key, value):
    config_factory(
        """
[bumpversion]
commit=true
""",
    )

    c = config.read(**{key: value})
    assert getattr(c, key) == value


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("release", True),
        ("commit", True),
        ("allow_dirty", True),
        ("reject_empty", True),
        ("date_format", "%Y-%m-%d"),
    ],
)
def test_read_overrides_pyproject(config_factory, key, value):
    config_factory("")

    c = config.read(**{key: value})
    assert getattr(c, key) == value


def test_process_overrides_no_post_process_values():
    _, post_process = config._process_overrides({})
    assert post_process is None


def test_process_overrides_extracts_post_process_values():
    overrides, post_process = config._process_overrides(
        {"key": "value", "post_process_url": "url", "post_process_auth_env": "auth"},
    )
    assert overrides == {"key": "value"}
    assert post_process.url == "url"
    assert post_process.auth_env == "auth"


def test_config_defaults():
    c = config.Config()
    assert c.verbose == 0
    assert c.version_string == "v{new_version}"
    assert c.allowed_branches == []
    assert c.commit_types == config.SUPPORTED_TYPES
    assert c.parser == re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")
    assert c.serialisers == ["{major}.{minor}.{patch}"]
    assert c.parts == {}
    assert c.files == {}

    for attr in [
        "issue_link",
        "commit_link",
        "date_format",
        "post_process",
    ]:
        assert getattr(c, attr) is None

    for attr in [
        "release",
        "commit",
        "tag",
    ]:
        assert getattr(c, attr) is True

    for attr in [
        "strict",
        "allow_dirty",
        "allow_missing",
        "reject_empty",
    ]:
        assert getattr(c, attr) is False

    assert c.semver_mappings == {
        "bug": "patch",
        "chore": "patch",
        "ci": "patch",
        "docs": "patch",
        "feat": "minor",
        "fix": "patch",
        "perf": "patch",
        "refactor": "patch",
        "revert": "patch",
        "style": "patch",
        "test": "patch",
    }
    assert c.type_headers == {
        "bug": "Bug fixes",
        "chore": "Miscellaneous",
        "ci": "Miscellaneous",
        "docs": "Documentation",
        "feat": "Features and Improvements",
        "fix": "Bug fixes",
        "perf": "Miscellaneous",
        "refactor": "Miscellaneous",
        "revert": "Miscellaneous",
        "style": "Miscellaneous",
        "test": "Miscellaneous",
    }


def test_post_process_defaults():
    pp = config.PostProcessConfig()
    assert pp.verb == "POST"
    assert pp.body == '{"body": "Released on ::version::"}'
    assert pp.auth_type == "basic"
    for attr in [
        "url",
        "headers",
        "auth_env",
    ]:
        assert getattr(pp, attr) is None


def test_commit_type():
    ct = config.CommitType("header", "semver")
    assert ct.header == "header"
    assert ct.semver == "semver"


def test_strict_validation():
    config.Config(
        strict=True,
        parser="""(?x)
(?P<major>0|[1-9]\\d*)\\.
(?P<minor>0|[1-9]\\d*)\\.
(?P<patch>0|[1-9]\\d*)
(?:
    (?P<release>[a-zA-Z-]+)       # pre-release label
    (?P<build>0|[1-9]\\d*)        # pre-release version number
)?                                # pre-release section is optional
""",
        serialisers=[
            "{major}.{minor}.{patch}-{release}{build}",
        ],
        parts={
            "release": ["rc"],
        },
    )


def test_strict_validation_incomplete_serialiser():
    with pytest.raises(
        errors.UnsupportedSerialiserError,
        match="Not all parsed components handled by a serialiser, missing {'build'}.",
    ):
        config.Config(
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<minor>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    (?:
        (?P<release>[a-zA-Z-]+)       # pre-release label
        (?P<build>0|[1-9]\\d*)        # pre-release version number
    )?                                # pre-release section is optional
    """,
            serialisers=[
                # No serialiser handles {build} scenario
                "{major}.{minor}.{patch}-{release}",
            ],
            parts={
                "release": ["rc"],
            },
        )


@pytest.mark.parametrize(
    "serialiser",
    [
        "{major}.{patch}",
        "{major}.{patch}{release}",
        "{major}.{minor}.{patch}{release}",
    ],
)
def test_strict_validation_bad_serialiser(serialiser):
    with pytest.raises(errors.UnsupportedSerialiserError, match=f"{serialiser} generates non RFC-2119 version string."):
        config.Config(
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<minor>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    (?:
        (?P<release>[a-zA-Z-]+)       # pre-release label
        (?P<build>0|[1-9]\\d*)        # pre-release version number
    )?                                # pre-release section is optional
    """,
            serialisers=[
                serialiser,
            ],
            parts={
                "release": ["rc"],
            },
        )


def test_strict_validation_bad_parser():
    with pytest.raises(errors.UnsupportedParserError, match="major.minor.patch, pattern required at minimum."):
        config.Config(
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    """,
        )
