import re

import pytest

from changelog_gen import config, errors


@pytest.fixture
def config_factory(cwd):
    def factory(contents=None):
        p = cwd / "pyproject.toml"
        p.touch()
        if contents:
            p.write_text(contents)

    return factory


@pytest.fixture
def pyproject_factory(cwd):
    def factory(contents=None):
        p = cwd / "pyproject.toml"
        p.touch()
        if contents:
            p.write_text(contents)

    return factory


@pytest.fixture
def _empty_config(config_factory):
    config_factory()


def test_read_handles_missing_file(cwd):
    p = cwd / "pyproject.toml"
    p.unlink()
    with pytest.raises(errors.ChangelogException):
        config.read()


@pytest.mark.usefixtures("_empty_config")
def test_read_handles_empty_file():
    with pytest.raises(errors.ChangelogException):
        config.read()


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
current_version = "0.0.0"
{value}
""",
        )

        c = config.read()
        assert getattr(c, exp_key) == exp_value

    def test_read_picks_up_strings_values(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
minor_regex = "feat|feature"
""",
        )

        c = config.read()
        assert c.minor_regex == "feat|feature"

    def test_read_picks_up_list_values(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
allowed_branches = [
    "main",
    "feature/11",
]
""",
        )

        c = config.read()
        assert c.allowed_branches == ["main", "feature/11"]

    def test_read_picks_custom_config(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
[tool.changelog_gen.custom]
key = "value"
key2 = "value2"
custom_list = ["one", "two"]
""",
        )

        c = config.read()
        assert c.custom == {
            "key": "value",
            "key2": "value2",
            "custom_list": ["one", "two"],
        }

    def test_read_picks_up_commit_types(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
commit_types = [
    {"type" = "bug", "header" = "Bug Fixes"},
    {"type" = "feature", "header" = "Features"},
    {"type" = "Fix", "header" = "Bug Fixes"},
]
""",
        )

        c = config.read()
        assert c.commit_types == [
            "feat",
            "fix",
            "bug",
            "docs",
            "chore",
            "ci",
            "perf",
            "refactor",
            "revert",
            "style",
            "test",
            "feature",
            "Fix",
        ]

    def test_read_picks_up_type_headers(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
commit_types = [
    {"type" = "bug", "header" = "Bug Fixes"},
    {"type" = "feature", "header" = "Features"},
    {"type" = "Fix", "header" = "Bug Fixes"},
]
""",
        )

        c = config.read()
        assert c.type_headers == {
            "Fix": "Bug Fixes",
            "bug": "Bug Fixes",
            "chore": "Miscellaneous",
            "ci": "Miscellaneous",
            "docs": "Documentation",
            "feat": "Features and Improvements",
            "feature": "Features",
            "fix": "Bug fixes",
            "perf": "Miscellaneous",
            "refactor": "Miscellaneous",
            "revert": "Miscellaneous",
            "style": "Miscellaneous",
            "test": "Miscellaneous",
        }

    def test_read_picks_up_github_config(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
[tool.changelog_gen.github]
strip_pr_from_description = true
extract_pr_from_description = true
extract_common_footers = true
""",
        )

        c = config.read()
        assert c.github == config.GithubConfig(
            strip_pr_from_description=True,
            extract_pr_from_description=True,
            extract_common_footers=True,
        )


class TestPostProcessConfig:
    def test_read_picks_up_no_post_process_config(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
release = true
        """,
        )

        c = config.read()
        assert c.post_process is None

    def test_read_picks_up_post_process_config_pyproject(self, config_factory):
        config_factory(
            r"""
[tool.changelog_gen]
current_version = "0.0.0"
[tool.changelog_gen.post_process]
link_generator."target" = "Refs"
link_generator."pattern" = '#(\d+)$'
link_generator."link" = "https://fake_rest_api/{0}"
verb = "PUT"
body_template = '{"issue": "{{ issue_ref }}", "comment": "Released in {{ version }}"}'
auth_env = "MY_API_AUTH"
headers."content-type" = "application/json"
""",
        )

        c = config.read()
        assert c.post_process == config.PostProcessConfig(
            link_generator={"target": "Refs", "pattern": r"#(\d+)$", "link": "https://fake_rest_api/{0}"},
            verb="PUT",
            body_template='{"issue": "{{ issue_ref }}", "comment": "Released in {{ version }}"}',
            auth_env="MY_API_AUTH",
            headers={"content-type": "application/json"},
        )

    def test_read_rejects_unknown_fields(self, config_factory):
        config_factory(
            """
[tool.changelog_gen]
current_version = "0.0.0"
[tool.changelog_gen.post_process]
enabled = false
""",
        )
        with pytest.raises(RuntimeError, match=r"^Failed to create post_process: .*"):
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
[tool.changelog_gen]
current_version = "0.0.0"
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
    config_factory(
        """
[tool.changelog_gen]
current_version = "0.0.0"
""",
    )

    c = config.read(**{key: value})
    assert getattr(c, key) == value


def test_config_defaults():
    c = config.Config(current_version="0.0.0")
    assert c.verbose == 0
    assert c.version_string == "v{new_version}"
    assert c.allowed_branches == []
    assert c.commit_types == list(config.SUPPORTED_TYPES.keys())
    assert c.type_headers == config.SUPPORTED_TYPES
    assert c.parser == re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)")
    assert c.serialisers == ["{major}.{minor}.{patch}"]
    assert c.parts == {}
    assert c.files == {}

    for attr in [
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
    assert pp.body_template == '{"body": "Released on {{ version }}"}'
    assert pp.auth_type == "basic"
    for attr in [
        "link_generator",
        "headers",
        "auth_env",
    ]:
        assert getattr(pp, attr) is None


def test_strict_validation():
    config.Config(
        current_version="0.0.0",
        strict=True,
        parser="""(?x)
(?P<major>0|[1-9]\\d*)\\.
(?P<minor>0|[1-9]\\d*)\\.
(?P<patch>0|[1-9]\\d*)
(?:
    (?P<release>[a-zA-Z-]+)       # pre-release label
    (?P<build>0|[1-9]\\d*)        # pre-release version number
)?                                # pre-release is optional
""",
        serialisers=[
            "{major}.{minor}.{patch}-{release}{build}",
        ],
        parts={
            "release": ["rc"],
        },
    )


def test_strict_validation_bad_parser():
    with pytest.raises(errors.UnsupportedParserError, match=r"major.minor.patch, pattern required at minimum."):
        config.Config(
            current_version="0.0.0",
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    """,
        )


def test_strict_validation_bad_parser_order():
    with pytest.raises(errors.UnsupportedParserError, match=r"major.minor.patch, pattern order required."):
        config.Config(
            current_version="0.0.0",
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)\\.
    (?P<minor>0|[1-9]\\d*)
    """,
        )


def test_strict_validation_incomplete_serialiser():
    with pytest.raises(
        errors.UnsupportedSerialiserError,
        match=r"Not all parsed components handled by a serialiser, missing {'build'}.",
    ):
        config.Config(
            current_version="0.0.0",
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<minor>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    (?:
        (?P<release>[a-zA-Z-]+)       # pre-release label
        (?P<build>0|[1-9]\\d*)        # pre-release version number
    )?                                # pre-release is optional
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
    with pytest.raises(
        errors.UnsupportedSerialiserError,
        match=f"{serialiser} generates non SemVer 2.0.0 version string.",
    ):
        config.Config(
            current_version="0.0.0",
            strict=True,
            parser="""(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<minor>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    (?:
        (?P<release>[a-zA-Z-]+)       # pre-release label
        (?P<build>0|[1-9]\\d*)        # pre-release version number
    )?                                # pre-release is optional
    """,
            serialisers=[
                serialiser,
            ],
            parts={
                "release": ["rc"],
            },
        )
