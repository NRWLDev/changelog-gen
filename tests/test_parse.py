import pytest

from changelog_gen import parse


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
            {"major": "0", "minor": "0", "patch": "0"},
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
    parsed = parse.parse(regex, version)
    assert parsed == expected
