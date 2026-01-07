import pytest

from changelog_gen import errors, version
from changelog_gen.config import Config, read


@pytest.fixture
def config_factory():
    def factory(**kwargs):
        if "current_version" not in kwargs:
            kwargs["current_version"] = "0.0.0"
        return Config(**kwargs)

    return factory


class TestModifyFile:
    def test_missing_file_raises(self, cwd):
        mf = version.ModifyFile("filename", cwd / "filename", [])

        with pytest.raises(errors.VersionError, match=r"Configured file not found 'filename'"):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_invalid_pattern_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["{invalid}"])

        with pytest.raises(errors.VersionError, match=r"Incorrect pattern '{invalid}' for 'filename'."):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_nullop_pattern_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["invalid"])

        with pytest.raises(errors.VersionError, match=r"Pattern 'invalid' generated no change for 'filename'."):
            mf.update("0.0.0", "0.0.1", dry_run=False)

    def test_pattern_no_change_raises(self, cwd):
        (cwd / "filename").write_text("0.0.0")
        mf = version.ModifyFile("filename", cwd / "filename", ["version = {version}"])

        with pytest.raises(
            errors.VersionError,
            match=r"No change for 'filename', ensure pattern 'version = {version}' is correct.",
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
            "current": "0.0.0",
            "new": "1.2.3",
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
            "current": current_version,
            "new": new_version,
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
            pre_release=True,
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
            "current": current_version,
            "new": new_version,
        }

    def test_replace(self, cwd):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[project]
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
        """.strip(),
        )
        cfg = read(str(p))

        new = "1.2.3"
        version.BumpVersion(cfg).replace(new)
        with p.open() as f:
            assert (
                f.read()
                == """[project]
version = "1.2.3"

[tool.changelog_gen]
current_version = "1.2.3"

[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'"""
            )

    def test_replace_dry_run(self, cwd):
        content = """
[project]
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

        new = "1.2.3"
        version.BumpVersion(cfg, dry_run=True).replace(new)
        with p.open() as f:
            assert f.read() == content

    def test_replace_invalid_pattern_reverts_files(self, cwd):
        content = """
[project]
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

        new = "1.2.3"
        with pytest.raises(errors.VersionError):
            version.BumpVersion(cfg).replace(new)

        with (cwd / "pyproject.toml").open() as f:
            assert f.read() == content
        with (cwd / "README.md").open() as f:
            assert f.read() == "0.0.0"

    def test_replace_invalid_pattern_dry_run(self, cwd):
        content = """
[project]
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

        new = "1.2.3"
        with pytest.raises(errors.VersionError):
            version.BumpVersion(cfg, dry_run=True).replace(new)

        with (cwd / "pyproject.toml").open() as f:
            assert f.read() == content
        with (cwd / "README.md").open() as f:
            assert f.read() == "0.0.0"

    def test_replace_returns_modified_files(self, cwd):
        p = cwd / "pyproject.toml"
        p.write_text(
            """
[project]
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

        new = "1.2.3"
        files = version.BumpVersion(cfg).replace(new)
        assert files == ["nested/README.md", "pyproject.toml"]
