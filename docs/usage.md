# Usage

## Getting started

If you have a project with no changelog currently, run `changelog init` to
generate an empty file.

If you have also not generated any releases yet, tag the repository with your
current version.  The current version is required to detect the correct semver
changes based on your commits.

A basic pyproject.toml configuration can be as simple as:

```toml
[tool.changelog_gen]
current_version = "0.0.0"
```

## Generating changelog

Run `changelog generate` to extract commits since the last release and populate
the changelog, and create a tagged release.

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

See [Configuration](/changelog-gen/configuration) for default commit type configuration
and how to customize them.

### CLI options and toggles

These options allow customising on a per run basis.

* `--version_tag` specify the version tag to release.
* `--version_part` specify the version component to increment.
* `--dry-run` extract changes and preview the proposed changelog and version
  without committing or tagging any changes.
* `--include-all` Include all commits, even incorrectly formatted ones, useful in combination with `--interactive`.
* `-y, --yes` accept proposed changes and commit without previewing, interactive
  mode will still be triggered prior to automatic acceptance.
* `-v[vv]` increase the output verbosity, handy if an error occurs or behaviour
  does not appear to match expectations.

The following toggles allow overriding configuration per run.

* `--interactive/--no-interactive` toggle configuration to drop into an editor with the proposed
  changes, to make any desired adjustments, prior to updating the changelog.
* `--allow-dirty/--no-allow-dirty` toggle configuration for allowing/rejecting git dirty status.
* `--allow-missing/--no-allow-missing` toggle configuration for allowing/rejecting missing commits in local/remote.
* `--reject-empty/--no-reject-empty` toggle configuration for updating configured files.
* `--release/--no-release` toggle configuration for updating configured files.
* `--commit/--no-commit` toggle configuration for committing changes.
* `--tag/--no-tag` toggle configuration for tagging release changes.

See [Configuration](/changelog-gen/configuration) for additional configuration and cli flags that are available.
and how to customize them.

## View current configuration

Use `changelog config` to view the currently configured values, including any
system defaults.
