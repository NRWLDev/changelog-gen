# Changelog Generator - v0.11.10
[![image](https://img.shields.io/pypi/v/changelog_gen.svg)](https://pypi.org/project/changelog_gen/)
[![image](https://img.shields.io/pypi/l/changelog_gen.svg)](https://pypi.org/project/changelog_gen/)
[![image](https://img.shields.io/pypi/pyversions/changelog_gen.svg)](https://pypi.org/project/changelog_gen/)
![style](https://github.com/NRWLDev/changelog-gen/actions/workflows/style.yml/badge.svg)
![tests](https://github.com/NRWLDev/changelog-gen/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/NRWLDev/changelog-gen/branch/main/graph/badge.svg)](https://codecov.io/gh/NRWLDev/changelog-gen)

# Details

`changelog-gen` is a CHANGELOG generator, to detect semantic versioning changes
from conventional commits, and generate release tags.

See the [docs](https://nrwldev.github.io/changelog-gen) for more details.

## Usage

`changelog init` will generate an empty changelog file if you have not been
maintaining changelogs previously. If you already have a changelog file, it
will be detected.

`changelog generate` will extract all commits matching the conventional format
since the last release, detect the correct semantic version component to
increment, and generate the correct changelog entry. Depending on
configuration, it will also update release tags in files as well as tagging the
release.

```bash
$ git log --oneline
a4e1449 feat: Open changes in editor before confirmation, to allow modification.
c314b6b feat: Block generation if local/remote are out of sync.
2e25deb chore: Relax typer version to 0.X
a95fd80 fix: Handle warning message from bump-my-version if setup.cfg exists
b46d2fe fix: Clean up link generation format in MDWriter
```

Using the above commits, can generate the following example changelog entry.

```md
# Changelog

## v0.9.2 - 2024-03-08

### Features and Improvements
- Open changes in editor before confirmation, to allow modification. [[#1](https://github.com/NRWLDev/changelog-gen/issues/1)] [[a4e1449](https://github.com/NRWLDev/changelog-gen/commit/a4e1449bf44f370c671cc679d4bf9cfd75e68cbf)]
- Block generation if local/remote are out of sync. [[#2](https://github.com/NRWLDev/changelog-gen/issues/2)] [[c314b6b](https://github.com/NRWLDev/changelog-gen/commit/c314b6b8a32f4ce5c05869f0accd24bb4e6097f2)]

### Bug fixes
- Handle warning message from bump-my-version if setup.cfg exists [[a95fd80](https://github.com/NRWLDev/changelog-gen/commit/a95fd80d939985ab4b51a864676dda234e345d47)]
- Clean up link generation format in MDWriter [[b46d2fe](https://github.com/NRWLDev/changelog-gen/commit/b46d2fe6fba5a170f25dffbf8697868d14a4e73e)]

### Miscellaneous
- Relax typer version to 0.X [[2e25deb](https://github.com/NRWLDev/changelog-gen/commit/2e25deb902710343a0f85f40323762752eef4a45)]
```

## Migrating from 0.8 to 0.9 (Conventional Commit support)
Check the discussion
[here](https://github.com/EdgyEdgemond/changelog-gen/discussions/98) for
details on how to update usage to maintain legacy functionality or move over to
new features.

## Installation

```bash
pip install changelog-gen
```

or clone this repo and install with invoke/poetry.

```bash
invoke install-dev
```

## Contributing

This project uses pre-commit hooks, please run `invoke install-dev` after
cloning to install dev dependencies and commit hooks.
