# Changelog Generator - v0.10.0
[![image](https://img.shields.io/pypi/v/changelog_gen.svg)](https://pypi.org/project/changelog_gen/)
[![image](https://img.shields.io/pypi/l/changelog_gen.svg)](https://pypi.org/project/changelog_gen/)
[![image](https://img.shields.io/pypi/pyversions/changelog_gen.svg)](https://pypi.org/project/changelog_gen/)
![style](https://github.com/NRWLDev/changelog-gen/actions/workflows/style.yml/badge.svg)
![tests](https://github.com/NRWLDev/changelog-gen/actions/workflows/tests.yml/badge.svg)
[![codecov](https://codecov.io/gh/NRWLDev/changelog-gen/branch/main/graph/badge.svg)](https://codecov.io/gh/NRWLDev/changelog-gen)

# Details

`changelog-gen` is a CHANGELOG generator intended to be used in conjunction
with [bump-my-version](https://github.com/callowayproject/bump-my-version) to generate
changelogs and create release tags.

See the [docs](https://nrwldev.github.io/changelog-gen) for more details.

## Usage

,2
## Migrating from 0.8 to 0.9 (Conventional Commit support)
Check the discussion
[here](https://github.com/EdgyEdgemond/changelog-gen/discussions/98) for
details on how to update usage to maintain legacy functionality or move over to
new features.

## Installation

```bash
pip install changelog-gen
```

or clone this repo and install with poetry.

```bash
poetry install
```

## Contributing

This project uses pre-commit hooks, please run `pre-commit install` after
cloning and installing dev dependencies.
