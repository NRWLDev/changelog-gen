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

## Conventional commits

```
<type>[(optional scope)][!]: <description>

[optional body]

[optional footer(s)]
```

`description` allows typical `[a-zA-Z ]` sentences, as well as `[.,/]`
punctuation, and ``[`]`` for highlighting words.

i.e.
```
fix: This is a valid description, with punctuation and a `highlighted` word.
```

Optional footers that are parsed by `changelog-gen` are:

* `BREAKING CHANGE:`
* `Refs: [#]<issue_ref>`
* `Authors: (<author>, ...)`

The description is used to populate the changelog file. If the type includes
the optional `!` flag, or the `BREAKING CHANGE` footer, this will lead to a
major release being suggested.

### Include all

Getting started with conventional commits can take some dedication, and its
easy to let some commits slip through the cracks. When generating changelogs
the `--include-all` flag is available to pick up all commits, even those that
don't fit the conventional commit format. All non conventional commits will be
included under a `Miscellaneous` heading. Combined with the `--interactive`
flag commits can be included under the correct headings and/or excluded
completely.

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

See [Configuration](/changelog-gen/configuration) below for default commit type configuration
and how to customize them.

### Configuration flags

* `--version_tag` specify the version tag to release.
* `--version_part` specify the version component to increment.
* `--dry-run` extract changes and preview the proposed changelog and version
  without committing or tagging any changes.
* `--interactive` flag can be used to drop into an editor with the proposed
  changes, to make any desired adjustments, prior to updating the changelog.
* `-y, --yes` accept proposed changes and commit without previewing, interactive
  mode will still be triggered prior to automatic acceptance.
* `-v[vv]` increase the output verbosity, handy if an error occurs or behaviour
  does not appear to match expectations.

See [Configuration](/changelog-gen/configuration) for additional configuration and cli flags that are available.
and how to customize them.

## View current configuration

Use `changelog config` to view the currently configured values, including any
system defaults.
