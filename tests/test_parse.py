import re

import pytest

from changelog_gen import errors, parse


def test_parse_failure():
    with pytest.raises(errors.ParseError):
        parse.parse(re.compile(r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"), "invalid")


@pytest.mark.parametrize(
    ("regex", "version", "expected"),
    [
        (
            r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)",
            "0.0.0",
            {"major": "0", "minor": "0", "patch": "0"},
        ),
        (
            r"""(?x)
                (?P<major>0|[1-9]\d*)\.
                (?P<minor>0|[1-9]\d*)\.
                (?P<patch>0|[1-9]\d*)
                (?:
                    (?P<release>rc)               # pre-release label
                    (?P<build>0|[1-9]\d*)         # pre-release version number
                )?                                # pre-release section is optional
            """,
            "0.0.0",
            {"major": "0", "minor": "0", "patch": "0", "release": None, "build": None},
        ),
        (
            r"""(?x)
                (?P<major>0|[1-9]\d*)\.
                (?P<minor>0|[1-9]\d*)\.
                (?P<patch>0|[1-9]\d*)
                (?:
                    (?P<release>rc)               # pre-release label
                    (?P<build>0|[1-9]\d*)         # pre-release version number
                )?                                # pre-release section is optional
            """,
            "0.0.0rc0",
            {"major": "0", "minor": "0", "patch": "0", "release": "rc", "build": "0"},
        ),
        (
            r"""(?x)
                (?P<major>0|[1-9]\d*)\.
                (?P<minor>0|[1-9]\d*)\.
                (?P<patch>0|[1-9]\d*)
                (?:
                    -                             # dash separator for pre-release section
                    (?P<pre_l>[a-zA-Z-]+)         # pre-release label
                    (?P<pre_n>0|[1-9]\d*)         # pre-release version number
                )?                                # pre-release section is optional
            """,
            "0.0.0",
            {"major": "0", "minor": "0", "patch": "0", "pre_l": None, "pre_n": None},
        ),
        (
            r"""(?x)
                (?P<major>0|[1-9]\d*)\.
                (?P<minor>0|[1-9]\d*)\.
                (?P<patch>0|[1-9]\d*)
                (?:
                    -                             # dash separator for pre-release section
                    (?P<pre_l>[a-zA-Z-]+)         # pre-release label
                    (?P<pre_n>0|[1-9]\d*)        # pre-release version number
                )?                                # pre-release section is optional
            """,
            "1.2.3-dev0",
            {"major": "1", "minor": "2", "patch": "3", "pre_l": "dev", "pre_n": "0"},
        ),
    ],
)
def test_parse(regex, version, expected):
    parsed = parse.parse(re.compile(regex), version)
    assert parsed == expected


def test_serialise_failure():
    with pytest.raises(errors.SerialiseError):
        parse.serialise(["{major}.{minor}.{patch}"], {"major": 1, "minor": 2})


@pytest.mark.parametrize(
    ("patterns", "version_parts", "expected"),
    [
        (
            [
                "{major}.{minor}.{patch}",
            ],
            {"major": "0", "minor": "0", "patch": "0"},
            "0.0.0",
        ),
        (
            [
                "{major}.{minor}.{patch}{release}{build}",
                "{major}.{minor}.{patch}",
            ],
            {"major": "0", "minor": "0", "patch": "0"},
            "0.0.0",
        ),
        (
            [
                "{major}.{minor}.{patch}{release}{build}",
                "{major}.{minor}.{patch}",
            ],
            {"major": "0", "minor": "0", "patch": "0", "release": "rc", "build": "0"},
            "0.0.0rc0",
        ),
        (
            [
                "{major}.{minor}.{patch}-{pre_l}{pre_n}",
                "{major}.{minor}.{patch}",
            ],
            {"major": "0", "minor": "0", "patch": "0"},
            "0.0.0",
        ),
        (
            [
                "{major}.{minor}.{patch}-{pre_l}{pre_n}",
                "{major}.{minor}.{patch}",
            ],
            {"major": "1", "minor": "2", "patch": "3", "pre_l": "dev", "pre_n": "0"},
            "1.2.3-dev0",
        ),
    ],
)
def test_serialise(patterns, version_parts, expected):
    serialised = parse.serialise(patterns, version_parts)
    assert serialised == expected


@pytest.mark.parametrize(
    ("version_parts", "component", "expected"),
    [
        (
            {"major": "0", "minor": "0", "patch": "0"},
            "patch",
            {"major": "0", "minor": "0", "patch": "1"},
        ),
        (
            {"major": "0", "minor": "0", "patch": "0"},
            "minor",
            {"major": "0", "minor": "1", "patch": "0"},
        ),
        (
            {"major": "0", "minor": "0", "patch": "1"},
            "minor",
            {"major": "0", "minor": "1", "patch": "0"},
        ),
        (
            {"major": "0", "minor": "9", "patch": "1"},
            "minor",
            {"major": "0", "minor": "10", "patch": "0"},
        ),
        (
            {"major": "0", "minor": "10", "patch": "1"},
            "minor",
            {"major": "0", "minor": "11", "patch": "0"},
        ),
        (
            {"major": "0", "minor": "0", "patch": "0"},
            "major",
            {"major": "1", "minor": "0", "patch": "0"},
        ),
        (
            {"major": "0", "minor": "1", "patch": "2"},
            "major",
            {"major": "1", "minor": "0", "patch": "0"},
        ),
    ],
)
def test_bump_vanilla(version_parts, component, expected):
    new_parts = parse.bump(version_parts, component, {}, pre_release=False)
    assert new_parts == expected


@pytest.mark.parametrize(
    ("version_parts", "component", "pre_release_components", "expected"),
    [
        (
            {"major": "0", "minor": "0", "patch": "0", "release": None, "build": None},
            "patch",
            ["major", "minor", "patch"],
            {"major": "0", "minor": "0", "patch": "1", "release": "dev", "build": "0"},
        ),
        (
            {"major": "0", "minor": "0", "patch": "0", "release": None, "build": None},
            "patch",
            ["major", "minor"],
            {"major": "0", "minor": "0", "patch": "1", "release": None, "build": None},
        ),
        (
            {"major": "0", "minor": "0", "patch": "0", "release": "rc", "build": "0"},
            "build",
            ["major", "minor", "patch"],
            {"major": "0", "minor": "0", "patch": "0", "release": "rc", "build": "1"},
        ),
        (
            {"major": "0", "minor": "0", "patch": "1", "release": "dev", "build": "1"},
            "release",
            ["major", "minor", "patch"],
            {"major": "0", "minor": "0", "patch": "1", "release": "rc", "build": "0"},
        ),
        (
            {"major": "0", "minor": "0", "patch": "1", "release": "rc", "build": "1"},
            "release",
            ["major", "minor", "patch"],
            {"major": "0", "minor": "0", "patch": "1", "release": None, "build": None},
        ),
    ],
)
def test_bump_configured_components(version_parts, component, pre_release_components, expected):
    new_parts = parse.bump(
        version_parts,
        component,
        component_config={"release": ["dev", "rc"]},
        pre_release_components=pre_release_components,
        pre_release=True,
    )
    assert new_parts == expected


@pytest.mark.parametrize(
    ("version_parts", "component", "expected"),
    [
        (
            {"major": "0", "minor": "0", "patch": "0", "release": None, "build": None},
            "patch",
            {"major": "0", "minor": "0", "patch": "1", "release": None, "build": None},
        ),
    ],
)
def test_bump_configured_components_no_pre_release(version_parts, component, expected):
    new_parts = parse.bump(version_parts, component, component_config={"release": ["dev", "rc"]}, pre_release=False)
    assert new_parts == expected


def test_bump_unset_optional_component():
    version_parts = {"major": "0", "minor": "0", "patch": "0", "release": None, "build": None}
    with pytest.raises(errors.BumpError):
        parse.bump(version_parts, "release", component_config={"release": ["dev", "rc"]}, pre_release=False)
