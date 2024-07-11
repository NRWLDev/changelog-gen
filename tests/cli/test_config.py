def test_config_displayed(cli_runner):
    result = cli_runner.invoke(["config"])

    assert result.exit_code == 0
    assert (
        result.output.strip()
        == r"""current_version = '0.0.0'
parser = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
verbose = 0
issue_link = 'null'
commit_link = 'null'
date_format = 'null'
version_string = 'v{new_version}'
release = false
commit = false
tag = false
allow_dirty = false
allow_missing = false
reject_empty = false
post_process = 'null'
serializers = ['{major}.{minor}.{patch}']
allowed_branches = []

[parts]

[files]
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
semver = 'patch'"""
    )
