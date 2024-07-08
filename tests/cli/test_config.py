def test_config_displayed(cli_runner):
    result = cli_runner.invoke(["config"])

    assert result.exit_code == 0
    assert (
        result.output.strip()
        == """verbose = 0
issue_link = 'https://github.com/NRWLDev/changelog-gen/issues/::issue_ref::'
commit_link = 'https://github.com/NRWLDev/changelog-gen/commit/::commit_hash::'
date_format = '- %Y-%m-%d'
version_string = 'v{new_version}'
release = true
commit = true
allow_dirty = false
allow_missing = false
reject_empty = true
post_process = 'null'
allowed_branches = [
    'main',
]
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
