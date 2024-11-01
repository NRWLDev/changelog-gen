import pytest


@pytest.fixture
def cwd(git_repo):
    return git_repo.workspace


@pytest.fixture
def multiversion_repo(git_repo):
    path = git_repo.workspace
    f = path / "hello.txt"
    f.write_text("hello world!")

    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("initial commit")

    git_repo.api.create_tag("v0.0.1")

    f.write_text("hello world! v2")
    git_repo.run("git add hello.txt")
    git_repo.api.index.commit("update")

    git_repo.api.create_tag("v0.0.2")

    return git_repo


@pytest.fixture
def conventional_commits(multiversion_repo):
    f = multiversion_repo.workspace / "hello.txt"
    hashes = []
    for msg in [
        """Fix(config): Detail about 4

Refs: #4
""",
        "fix typo",
        """feat(docs)!: Detail about 3

Fixes #3
""",
        """fix: Detail about 1

With some details

BREAKING CHANGE:
Refs: #1
""",
        "update readme",
        """feat: Detail about 2 (#2)

Authors: @tom, @edgy
closes #2
""",
    ]:
        f.write_text(msg)
        multiversion_repo.run("git add hello.txt")
        multiversion_repo.api.index.commit(msg)
        hashes.append(str(multiversion_repo.api.head.commit))
    return hashes


@pytest.fixture
def pyproject(cwd):
    p = cwd / "pyproject.toml"
    p.write_text(
        r"""
[tool.changelog_gen]
current_version = "0.0.2"
change_template = '''
-{% if change.scope %} (`{{change.scope}}`){% endif %}
{% if change.breaking %} **Breaking**{% endif %}
 {{ change.description | regex_replace('MPL-\d+ - ', '')}}
{% for footer in change.footers %}{% if footer.footer == "Authors"%} {{footer.value}}{% endif %}{% endfor %}
{% for link in change.links %} [[{{ link.text }}]({{ link.link }})]{% endfor %}
'''
release_template = '''
## {{ version_string }}

{% for header, changes in group_changes.items() -%}
### {{ header }}

{% for change in changes -%}
{{change.rendered}}
{% endfor %}
{% endfor %}
'''
""",
    )

    return p


@pytest.mark.usefixtures("pyproject")
def test_change_template(cli_runner, conventional_commits):
    hashes = conventional_commits
    result = cli_runner.invoke(["test", hashes[2], "--template", "change"])

    assert result.exit_code == 0, result.output
    assert (
        result.output.strip()
        == r"""
- (`docs`) **Breaking** Detail about 3
""".strip()
    )


@pytest.mark.usefixtures("pyproject")
def test_release_template(cli_runner, conventional_commits):
    hashes = conventional_commits
    result = cli_runner.invoke(["test", hashes[2], "--template", "release"])

    assert result.exit_code == 0, result.output
    assert (
        result.output.strip()
        == r"""## v0.0.0

### Features and Improvements

- Detail about 2 (#2) @tom, @edgy

### Bug fixes

- **Breaking** Detail about 1
""".strip()
    )
