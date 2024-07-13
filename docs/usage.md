# Usage

## Getting started

If you have a project with no changelog currently, run `changelog init` to
generate an empty file.

If you have also not generated any releases yet, tag the repository with your
current version.  The current version is required to detect the correct semver
changes based on your commits.

A basic pyproject.toml configuration can be as simple as:

```toml
[tool.poetry]
name = "my-project"
version = "0.0.0"

[tool.changelog_gen]
current_version = "0.0.0"
reject_empty = true
allowed_branches = [
    "main",
]

[[tool.bumpversion.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
```

## Generating changelog

Run `changelog generate` to extract commits since the last release and populate
the changelog, and create a tagged release.

```md
## <version>

### Features and Improvements
- xxx
- xxx

### Bug fixes
- xxx
- xxx

### Documentation
- xxx
- xxx

### Miscellaneous
- xxx
- xxx
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
