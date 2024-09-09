import os
import pathlib

import pytest
import rtoml


@pytest.fixture
def cwd(tmp_path):
    orig = pathlib.Path.cwd()

    try:
        os.chdir(str(tmp_path))
        yield tmp_path
    finally:
        os.chdir(orig)


@pytest.fixture
def git_repo(git_repo):
    git_repo.run("git config user.email 'you@example.com'")
    git_repo.run("git config user.name 'Your Name'")
    git_repo.run("git checkout -b main")

    orig = pathlib.Path.cwd()

    try:
        os.chdir(str(git_repo.workspace))
        yield git_repo
    finally:
        os.chdir(orig)


@pytest.fixture
def config_factory(cwd):
    def factory(**config):
        p = cwd / "pyproject.toml"
        config["current_version"] = "0.0.0"

        data = {
            "tool": {
                "changelog_gen": config,
            },
        }
        with p.open("w") as f:
            rtoml.dump(data, f)

    return factory


@pytest.fixture(autouse=True)
def config(config_factory):
    return config_factory()
