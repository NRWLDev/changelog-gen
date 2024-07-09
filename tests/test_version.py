from unittest import mock

import pytest

from changelog_gen import errors, version


class TestBumpMyVersion:
    @pytest.mark.usefixtures("cwd")
    def test_version_info_handles_errors(self):
        with pytest.raises(errors.VersionError) as e:
            version.BumpVersion().get_version_info("patch")

        assert (
            str(e.value)
            == """Unable to get version data from bumpversion.
error: Unable to determine the current version."""
        )

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
    def test_get_version_info(self, cwd, current_version, new_version, semver):
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

        assert version.BumpVersion().get_version_info(semver) == {
            "current": cv,
            "current_str": current_version,
            "new": nv,
            "new_str": new_version,
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
    def test_get_version_info_release_flow(self, cwd, current_version, new_version, semver):
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

        assert version.BumpVersion().get_version_info(semver) == {
            "current": cv,
            "current_str": current_version,
            "new": nv,
            "new_str": new_version,
        }

    def test_replace(self, cwd):
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

        current = config.version_config.parse("0.0.0")
        new = config.version_config.parse("1.2.3")
        version.BumpVersion().replace(current, new)
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
    def test_replace_config_kwargs(self, cwd, kwargs, expected_kwargs, monkeypatch):
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

        current = config.version_config.parse("0.0.0")
        new = config.version_config.parse("1.2.3")
        version.BumpVersion(**kwargs).replace(current, new)

        assert version.get_configuration.call_args == mock.call(
            version.find_config_file.return_value,
            **expected_kwargs,
        )

    @pytest.mark.usefixtures("cwd")
    def test_replace_handles_configuration_error(self, monkeypatch):
        monkeypatch.setattr(version.logger, "warning", mock.Mock())
        current = {"major": mock.Mock(value=0), "minor": mock.Mock(value=0), "patch": mock.Mock(value=0)}
        new = {"major": mock.Mock(value=1), "minor": mock.Mock(value=2), "patch": mock.Mock(value=3)}
        with pytest.raises(errors.VersionError) as e:
            version.BumpVersion().replace(current, new)

        assert (
            str(e.value)
            == """Unable to modify files with bumpversion.
error: Unable to determine the current version."""
        )
