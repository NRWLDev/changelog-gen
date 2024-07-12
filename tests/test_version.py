from unittest import mock

import pytest

try:
    import bumpversion  # noqa: F401

    bump_not_installed = False
except ImportError:
    bump_not_installed = True

from changelog_gen import errors, version
from changelog_gen.config import Config, read


@pytest.fixture()
def cfg():
    return Config()


@pytest.fixture()
def config_factory():
    def factory(**kwargs):
        return Config(**kwargs)

    return factory


class TestModifyFile:
    def test_missing_file_raises(self, cwd):
        mf = version.ModifyFile("filename", cwd / "filename", [])

        with pytest.raises(errors.VersionError, match="Configured file not found 'filename'"):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_invalid_pattern_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["{invalid}"])

        with pytest.raises(errors.VersionError, match="Incorrect pattern '{invalid}' for 'filename'."):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_nullop_pattern_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["invalid"])

        with pytest.raises(errors.VersionError, match="Pattern 'invalid' generated no change for 'filename'."):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_pattern_no_change_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["version = {version}"])

        with pytest.raises(
            errors.VersionError,
            match="No change for 'filename', ensure pattern 'version = {version}' is correct.",
        ):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_update_applies_multiple_updates(self, cwd):
        (cwd / "filename").write_text('version1 = "0.0.0"\nversion2 = "0.0.0"')
        mf = version.ModifyFile("filename", cwd / "filename", ['version1 = "{version}"', 'version2 = "{version}'])

        mf.update("0.0.0", "0.0.1", dry_run=False)

        assert (cwd / "filename.bak").read_text() == 'version1 = "0.0.1"\nversion2 = "0.0.1"'

    def test_update_writes_to_backup(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["{version}"])

        original, backup = mf.update("0.0.0", "0.0.1", dry_run=False)

        assert (cwd / "filename").read_text() == "0.0.0"
        assert original.read_text() == "0.0.0"
        assert backup.read_text() == "0.0.1"


class TestInHouse:
    def test_get_version_info_uses_provided_version(self, config_factory):
        cfg = config_factory(current_version="0.0.0")

        assert version.BumpVersion(cfg, new="1.2.3").get_version_info("patch") == {
            "current": version.Version("0.0.0", None),
            "new": version.Version("1.2.3", None),
        }

    @pytest.mark.parametrize(
        ("current_version", "new_version", "semver"),
        [
            ("0.0.0", "0.0.1", "patch"),
            ("0.1.0", "0.1.1", "patch"),
            ("1.2.3", "1.2.4", "patch"),
            ("1.2.3", "1.3.0", "minor"),
            ("1.2.3", "2.0.0", "major"),
        ],
    )
    def test_get_version_info(self, current_version, new_version, semver, config_factory):
        cfg = config_factory(current_version=current_version)

        assert version.BumpVersion(cfg).get_version_info(semver) == {
            "current": version.Version(current_version, None),
            "new": version.Version(new_version, None),
        }

    @pytest.mark.parametrize(
        ("current_version", "new_version", "semver"),
        [
            ("0.0.0", "0.0.1rc0", "patch"),
            ("0.1.0", "0.1.1rc0", "patch"),
            ("1.2.3", "1.2.4rc0", "patch"),
            ("1.2.3", "1.3.0rc0", "minor"),
            ("1.2.3", "2.0.0rc0", "major"),
            ("1.2.3rc0", "1.2.3rc1", "build"),
            ("1.2.3rc1", "1.2.3rc2", "build"),
            ("1.2.3rc1", "1.2.3", "release"),
        ],
    )
    def test_get_version_info_release_flow(self, current_version, new_version, semver, config_factory):
        cfg = config_factory(
            current_version=current_version,
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
                "{major}.{minor}.{patch}{release}{build}",
                "{major}.{minor}.{patch}",
            ],
            parts={
                "release": ["rc"],
            },
        )

        assert version.BumpVersion(cfg).get_version_info(semver) == {
            "current": version.Version(current_version, None),
            "new": version.Version(new_version, None),
        }

    def test_replace(self, cwd):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.poetry]
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip(),
        )
        cfg = read(str(p))

        current = version.Version("0.0.0", None)
        new = version.Version("1.2.3", None)
        version.BumpVersion(cfg).replace(current, new)
        with p.open() as f:
            assert (
                f.read()
                == """[tool.poetry]
version = "1.2.3"

[tool.changelog_gen]
current_version = "1.2.3"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'"""
            )

    def test_replace_dry_run(self, cwd):
        content = """
[tool.poetry]
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip()

        p = cwd / "pyproject.toml"
        p.write_text(content)
        cfg = read(str(p))

        current = version.Version("0.0.0", None)
        new = version.Version("1.2.3", None)
        version.BumpVersion(cfg, dry_run=True).replace(current, new)
        with p.open() as f:
            assert f.read() == content

    def test_replace_invalid_pattern_reverts_files(self, cwd):
        content = """
[tool.poetry]
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"

[[tool.changelog_gen.files]]
filename = "README.md"
pattern = "{invalid}"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip()

        (cwd / "README.md").write_text("0.0.0")
        p = cwd / "pyproject.toml"
        p.write_text(content)
        cfg = read(str(p))

        current = version.Version("0.0.0", None)
        new = version.Version("1.2.3", None)
        with pytest.raises(errors.VersionError):
            version.BumpVersion(cfg).replace(current, new)

        with (cwd / "pyproject.toml").open() as f:
            assert f.read() == content
        with (cwd / "README.md").open() as f:
            assert f.read() == "0.0.0"

    def test_replace_invalid_pattern_dry_run(self, cwd):
        content = """
[tool.poetry]
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"

[[tool.changelog_gen.files]]
filename = "README.md"
pattern = "{invalid}"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip()
        (cwd / "README.md").write_text("0.0.0")
        p = cwd / "pyproject.toml"
        p.write_text(content)
        cfg = read(str(p))

        current = version.Version("0.0.0", None)
        new = version.Version("1.2.3", None)
        with pytest.raises(errors.VersionError):
            version.BumpVersion(cfg, dry_run=True).replace(current, new)

        with (cwd / "pyproject.toml").open() as f:
            assert f.read() == content
        with (cwd / "README.md").open() as f:
            assert f.read() == "0.0.0"

    def test_replace_returns_modified_files(self, cwd):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.poetry]
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'

[[tool.changelog_gen.files]]
filename = "nested/README.md"
        """.strip(),
        )
        cfg = read(str(p))

        p = cwd / "nested"
        p.mkdir()
        r = p / "README.md"
        r.write_text("Hello 0.0.0")

        current = version.Version("0.0.0", None)
        new = version.Version("1.2.3", None)
        files = version.BumpVersion(cfg).replace(current, new)
        assert files == ["nested/README.md", "pyproject.toml"]


@pytest.mark.skipif(bump_not_installed, reason="bumpversion not installed")
@pytest.mark.backwards_compat()
class TestBumpMyVersion:
    def setUp(self):
        pytest.importorskip("bumpversion")

    @pytest.mark.usefixtures("cwd")
    def test_version_info_handles_errors(self, cfg):
        with pytest.raises(errors.VersionError) as e:
            version.BumpVersion(cfg).get_version_info("patch")

        assert (
            str(e.value)
            == """Unable to get version data from bumpversion.
error: Unable to determine the current version."""
        )

    def test_get_version_info_uses_provided_version(self, cwd, cfg):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.bumpversion]
current_version = "0.0.0"
        """.strip(),
        )

        config = version.get_configuration(str(p))
        cv = config.version_config.parse("0.0.0")
        nv = config.version_config.parse("1.2.3")

        assert version.BumpVersion(cfg, new="1.2.3").get_version_info("patch") == {
            "current": version.Version("0.0.0", cv),
            "new": version.Version("1.2.3", nv),
        }

    @pytest.mark.parametrize(
        ("current_version", "new_version", "semver"),
        [
            ("0.0.0", "0.0.1", "patch"),
            ("0.1.0", "0.1.1", "patch"),
            ("1.2.3", "1.2.4", "patch"),
            ("1.2.3", "1.3.0", "minor"),
            ("1.2.3", "2.0.0", "major"),
        ],
    )
    def test_get_version_info(self, cwd, current_version, new_version, semver, cfg):
        p = cwd / "pyproject.toml"
        p.write_text(
            f"""
[tool.bumpversion]
current_version = "{current_version}"
        """.strip(),
        )

        config = version.get_configuration(str(p))
        cv = config.version_config.parse(current_version)
        nv = config.version_config.parse(new_version)

        assert version.BumpVersion(cfg).get_version_info(semver) == {
            "current": version.Version(current_version, cv),
            "new": version.Version(new_version, nv),
        }

    @pytest.mark.parametrize(
        ("current_version", "new_version", "semver"),
        [
            ("0.0.0", "0.0.1rc0", "patch"),
            ("0.1.0", "0.1.1rc0", "patch"),
            ("1.2.3", "1.2.4rc0", "patch"),
            ("1.2.3", "1.3.0rc0", "minor"),
            ("1.2.3", "2.0.0rc0", "major"),
            ("1.2.3rc0", "1.2.3rc1", "build"),
            ("1.2.3rc1", "1.2.3rc2", "build"),
            ("1.2.3rc1", "1.2.3", "release"),
        ],
    )
    def test_get_version_info_release_flow(self, cwd, current_version, new_version, semver, cfg):
        p = cwd / "pyproject.toml"
        p.write_text(
            f"""
[tool.bumpversion]
current_version = "{current_version}"
commit = false
tag = false
parse = '''(?x)
    (?P<major>0|[1-9]\\d*)\\.
    (?P<minor>0|[1-9]\\d*)\\.
    (?P<patch>0|[1-9]\\d*)
    (?:
        (?P<release>[a-zA-Z-]+)       # pre-release label
        (?P<build>0|[1-9]\\d*)        # pre-release version number
    )?                                # pre-release section is optional
'''
serialize = [
    "{{major}}.{{minor}}.{{patch}}{{release}}{{build}}",
    "{{major}}.{{minor}}.{{patch}}",
]
parts.release.values = ["rc", "final"]
parts.release.optional_value = "final"
        """.strip(),
        )
        config = version.get_configuration(str(p))
        cv = config.version_config.parse(current_version)
        nv = config.version_config.parse(new_version)

        assert version.BumpVersion(cfg).get_version_info(semver) == {
            "current": version.Version(current_version, cv),
            "new": version.Version(new_version, nv),
        }

    def test_replace(self, cwd, cfg):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.poetry]
version = "0.0.0"

[tool.bumpversion]
current_version = "0.0.0"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'
        """.strip(),
        )
        config = version.get_configuration(str(p))

        current = version.Version("0.0.0", config.version_config.parse("0.0.0"))
        new = version.Version("1.2.3", config.version_config.parse("1.2.3"))
        version.BumpVersion(cfg).replace(current, new)
        with p.open() as f:
            assert (
                f.read()
                == """[tool.poetry]
version = "1.2.3"

[tool.bumpversion]
current_version = "1.2.3"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'"""
            )

    @pytest.mark.parametrize(
        ("kwargs", "expected_kwargs"),
        [
            ({}, {"dry_run": False, "allow_dirty": False}),
            ({"dry_run": True}, {"dry_run": True, "allow_dirty": False}),
            ({"allow_dirty": True}, {"dry_run": False, "allow_dirty": True}),
        ],
    )
    def test_replace_config_kwargs(self, cwd, kwargs, expected_kwargs, monkeypatch, cfg):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[tool.bumpversion]
current_version = "0.0.0"
        """.strip(),
        )
        monkeypatch.setattr(version, "find_config_file", mock.Mock())
        config = version.get_configuration(str(p))
        monkeypatch.setattr(version, "get_configuration", mock.Mock(return_value=config))

        current = version.Version("0.0.0", config.version_config.parse("0.0.0"))
        new = version.Version("1.2.3", config.version_config.parse("1.2.3"))
        version.BumpVersion(cfg, **kwargs).replace(current, new)

        assert version.get_configuration.call_args == mock.call(
            version.find_config_file.return_value,
            **expected_kwargs,
        )

    @pytest.mark.usefixtures("cwd")
    def test_replace_handles_configuration_error(self, monkeypatch, cfg):
        monkeypatch.setattr(version.logger, "warning", mock.Mock())
        current = {"major": mock.Mock(value=0), "minor": mock.Mock(value=0), "patch": mock.Mock(value=0)}
        new = {"major": mock.Mock(value=1), "minor": mock.Mock(value=2), "patch": mock.Mock(value=3)}
        current = version.Version("0.0.0", current)
        new = version.Version("1.2.3", new)
        with pytest.raises(errors.VersionError) as e:
            version.BumpVersion(cfg).replace(current, new)

        assert (
            str(e.value)
            == """Unable to modify files with bumpversion.
error: Unable to determine the current version."""
        )
