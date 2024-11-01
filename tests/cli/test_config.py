def test_config_displayed(cli_runner):
    result = cli_runner.invoke(["config"])

    assert result.exit_code == 0
    assert (
        result.output.strip()
        == r"""current_version = '0.0.0'
verbose = 0
interactive = true
release = true
commit = true
tag = true
allow_dirty = false
allow_missing = false
reject_empty = false
statistics = false
minor_regex = 'feat'
parser = '(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)'
strict = false
pre_release = false
version_string = 'v{new_version}'
allowed_branches = []
commit_types = [
    'feat',
    'fix',
    'bug',
    'docs',
    'chore',
    'ci',
    'perf',
    'refactor',
    'revert',
    'style',
    'test',
]
serialisers = ['{major}.{minor}.{patch}']
footer_parsers = [
    '(Refs)(: )(#?[\w-]+)',
    '(Authors)(: )(.*)',
]
hooks = []
link_generators = []
extractors = []

[type_headers]
feat = 'Features and Improvements'
fix = 'Bug fixes'
bug = 'Bug fixes'
docs = 'Documentation'
chore = 'Miscellaneous'
ci = 'Miscellaneous'
perf = 'Miscellaneous'
refactor = 'Miscellaneous'
revert = 'Miscellaneous'
style = 'Miscellaneous'
test = 'Miscellaneous'

[parts]

[custom]

[files]"""
    )


def test_post_process_config_displayed(cli_runner, config_factory):
    config_factory(post_process={"link_generator": {"target": "Refs", "link": "http://localhost"}})
    result = cli_runner.invoke(["config"])

    assert result.exit_code == 0
    assert result.output.endswith("""
[post_process]
verb = 'POST'
body_template = '{"body": "Released on {{ version }}"}'
auth_type = 'basic'

[post_process.link_generator]
target = 'Refs'
link = 'http://localhost'

[custom]

[files]

""")


def test_config_key_displayed(cli_runner):
    result = cli_runner.invoke(["config", "--key", "commit_types"])

    assert result.exit_code == 0
    assert (
        result.output.strip()
        == r"""commit_types = [
    'feat',
    'fix',
    'bug',
    'docs',
    'chore',
    'ci',
    'perf',
    'refactor',
    'revert',
    'style',
    'test',
]"""
    )
