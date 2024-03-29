import pytest


@pytest.fixture()
def setup(cwd):
    p = cwd / "setup.cfg"
    p.write_text(
        """
[changelog_gen]
release = true
commit = true
allow_dirty = false
reject_empty = false
allowed_branches = main, test
section_mapping =
    bug=fix
    ci=misc
    docs=docs
    refactor=misc
    revert=misc
    style=misc
    test=misc
version_string={new_version}
date_format=on %%Y-%%b-%%d
issue_link = https://github.com/EdgyEdgemond/changelog-gen/issues/{issue_ref}
commit_link = https://github.com/EdgyEdgemond/changelog-gen/issues/{commit_hash}
post_process=
    url=http://url
    verb=PUT
    body={{"body": "version {new_version}"}}
    headers={"content-type": "application/json"}
    auth_env=AUTH_KEY

""",
    )

    return cwd


@pytest.fixture()
def simple_setup(cwd):
    p = cwd / "setup.cfg"
    p.write_text(
        """
[changelog_gen]
release = true
commit = true
allow_dirty = false
reject_empty = false
allowed_branches = main
version_string={new_version}
date_format=on %%Y-%%b-%%d
issue_link = https://github.com/EdgyEdgemond/changelog-gen/issues/::issue_ref::
commit_link = https://github.com/EdgyEdgemond/changelog-gen/issues/::commit_hash::

""",
    )

    return cwd


@pytest.mark.usefixtures("setup")
def test_migrate_generates_toml(cli_runner):
    result = cli_runner.invoke(["migrate"])

    assert result.exit_code == 0
    assert (
        result.output
        == """[tool.changelog_gen]
issue_link = "https://github.com/EdgyEdgemond/changelog-gen/issues/::issue_ref::"
commit_link = "https://github.com/EdgyEdgemond/changelog-gen/issues/::commit_hash::"
date_format = "on %Y-%b-%d"
version_string = "{new_version}"
release = true
commit = true
allowed_branches = ["main", "test"]

[tool.changelog_gen.post_process]
url = "http://url"
verb = "PUT"
body = "{\\"body\\": \\"version ::version::\\"}"
auth_env = "AUTH_KEY"

[tool.changelog_gen.post_process.headers]
content-type = "application/json"
[tool.changelog_gen.commit_types.feat]
header = "Features and Improvements"
semver = "minor"

[tool.changelog_gen.commit_types.fix]
header = "Bug fixes"
semver = "patch"

[tool.changelog_gen.commit_types.docs]
header = "Documentation"
semver = "patch"

[tool.changelog_gen.commit_types.misc]
header = "Miscellaneous"
semver = "patch"

[tool.changelog_gen.commit_types.bug]
header = "Bug fixes"
semver = "patch"

[tool.changelog_gen.commit_types.ci]
header = "Miscellaneous"
semver = "patch"

[tool.changelog_gen.commit_types.refactor]
header = "Miscellaneous"
semver = "patch"

[tool.changelog_gen.commit_types.revert]
header = "Miscellaneous"
semver = "patch"

[tool.changelog_gen.commit_types.style]
header = "Miscellaneous"
semver = "patch"

[tool.changelog_gen.commit_types.test]
header = "Miscellaneous"
semver = "patch"

"""
    )


@pytest.mark.usefixtures("simple_setup")
def test_migrate_generates_toml_simple_setup(cli_runner):
    result = cli_runner.invoke(["migrate"])

    assert result.exit_code == 0
    assert (
        result.output
        == """[tool.changelog_gen]
issue_link = "https://github.com/EdgyEdgemond/changelog-gen/issues/::issue_ref::"
commit_link = "https://github.com/EdgyEdgemond/changelog-gen/issues/::commit_hash::"
date_format = "on %Y-%b-%d"
version_string = "{new_version}"
release = true
commit = true
allowed_branches = ["main"]

"""
    )


@pytest.mark.usefixtures("cwd")
def test_migrate_no_setup(cli_runner):
    result = cli_runner.invoke(["migrate"])

    assert result.exit_code == 1
    assert result.output.strip() == "setup.cfg not found."
