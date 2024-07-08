from unittest import mock

import pytest

from changelog_gen import errors, version


def test_info():
    assert version.parse_info(
        "patch",
        [
            "1.2.3 -- bump -+- major --- 2.0.0rc0",
            "               +- minor --- 1.3.0rc0",
            "               +- patch --- 1.2.4rc0",
            '               +- release - invalid: The part has already the maximum value among ["rc", "final"] and cannot be bumped.',  # noqa: E501
            "               +- build --- 1.2.3final1",
        ],
    ) == ("1.2.3", "1.2.4rc0")


def test_parse_info_handles_setup_cfg():
    assert version.parse_info(
        "patch",
        [
            "WARNING:",
            "",
            "setup.cfg is deprecated message.",
            "",
            "1.2.3 -- bump -+- major --- 2.0.0rc0",
            "               +- minor --- 1.3.0rc0",
            "               +- patch --- 1.2.4rc0",
            '               +- release - invalid: The part has already the maximum value among ["rc", "final"] and cannot be bumped.',  # noqa: E501
            "               +- build --- 1.2.3final1",
        ],
    ) == ("1.2.3", "1.2.4rc0")


@pytest.mark.parametrize(
    ("verbose", "expected_verbosity"),
    [
        (1, ["-v"]),
        (2, ["-vv"]),
        (3, ["-vvv"]),
    ],
)
def test_generate_verbosity(verbose, expected_verbosity):
    assert version.generate_verbosity(verbose) == expected_verbosity


class TestBumpMyVersion:
    @pytest.mark.usefixtures("cwd")
    def test_version_info_handles_errors(self):
        with pytest.raises(errors.VersionError) as e:
            version.BumpVersion().get_version_info("patch")

        assert (
            str(e.value)
            == """Unable to get version data from bumpversion.
cmd: bump-my-version show-bump --ascii
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
commit = false
tag = false
        """.strip(),
        )

        assert version.BumpVersion().get_version_info(semver) == {"current": current_version, "new": new_version}

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

        assert version.BumpVersion().get_version_info(semver) == {"current": current_version, "new": new_version}

    @pytest.mark.parametrize(
        ("kwargs", "expected_command_args"),
        [
            ({}, []),
            ({"dry_run": True}, ["--dry-run"]),
            ({"allow_dirty": True}, ["--allow-dirty"]),
            ({"verbose": 3}, ["-vvv"]),
        ],
    )
    def test_release(self, monkeypatch, kwargs, expected_command_args):
        monkeypatch.setattr(version.subprocess, "check_output", mock.Mock(return_value=b""))
        version.BumpVersion(**kwargs).release("1.2.3")
        assert version.subprocess.check_output.call_args == mock.call(
            ["bump-my-version", "bump", "patch", "--new-version", "1.2.3"] + expected_command_args,  # noqa: RUF005
            stderr=version.subprocess.STDOUT,
        )

    @pytest.mark.usefixtures("cwd")
    def test_release_handles_error(self, monkeypatch):
        monkeypatch.setattr(version.logger, "warning", mock.Mock())
        with pytest.raises(errors.VersionError) as e:
            version.BumpVersion().release("1.2.3")

        assert (
            str(e.value)
            == """Unable to generate release with bumpversion.
cmd: bump-my-version bump patch --new-version 1.2.3
error: Unable to determine the current version."""
        )
