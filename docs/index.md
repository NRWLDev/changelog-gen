# Overview

`changelog-gen` is a CHANGELOG generator intended to remove the mental load of
determining correct versioning, while generating changelogs and creating release
tags from [conventional commit](https://www.conventionalcommits.org/en/v1.0.0/)
formatted commit messages.

Usage of `bump-my-version` for version management is being deprecated, and
brought in to `changelog_gen` to reduce the dependency chain, and allow more
control of versioning.

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

## Installation

```bash
pip install changelog-gen

pip install changelog-gen[legacy]       # legacy bump-my-version support
pip install changelog-gen[post-process] # include httpx support for post-process hooks
```
