def test_config_displayed(cli_runner):
    result = cli_runner.invoke(["config"])

    assert result.exit_code == 0
    assert (
        result.output.strip()
        == r"""current_version = '0.0.0'
parser = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
strict = false
verbose = 0
version_string = 'v{new_version}'
interactive = true
release = true
commit = true
tag = true
allow_dirty = false
allow_missing = false
reject_empty = false
pre_release = false
serialisers = ['{major}.{minor}.{patch}']
allowed_branches = []
hooks = []

[parts]
[commit_types.feat]
header = 'Features and Improvements'
semver = 'minor'

[commit_types.fix]
header = 'Bug fixes'
semver = 'patch'

[commit_types.bug]
header = 'Bug fixes'
semver = 'patch'

[commit_types.docs]
header = 'Documentation'
semver = 'patch'

[commit_types.chore]
header = 'Miscellaneous'
semver = 'patch'

[commit_types.ci]
header = 'Miscellaneous'
semver = 'patch'

[commit_types.perf]
header = 'Miscellaneous'
semver = 'patch'

[commit_types.refactor]
header = 'Miscellaneous'
semver = 'patch'

[commit_types.revert]
header = 'Miscellaneous'
semver = 'patch'

[commit_types.style]
header = 'Miscellaneous'
semver = 'patch'

[commit_types.test]
header = 'Miscellaneous'
semver = 'patch'

[files]"""
    )


def test_post_process_config_displayed(cli_runner, config_factory):
    config_factory(post_process={"url": "http://localhost"})
    result = cli_runner.invoke(["config"])

    assert result.exit_code == 0
    assert result.output.strip().endswith("""
[post_process]
url = 'http://localhost'
verb = 'POST'
body = '{"body": "Released on ::version::"}'
auth_type = 'basic'

[files]""")
