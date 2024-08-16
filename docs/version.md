# Semantic Versioning

At the core of `changelog-gen` is the version detection and generation logic,
check [here](https://semver.org) for details on semantic versioning.

## Version generation

`changelog-gen` uses conventional commit types and its own configuration to
determine what type of release to trigger based on the commits since the last release.

### Major

Any breaking change will trigger a major release, unless the package is in the
initial `0.y.z` development release. In commit terms, any commit message with a
`!` suffix in the type, or `BREAKING CHANGE` in the footers is considered a
breaking change.

### Minor

New features, will trigger a minor release (or patch while in the development
release). Feature commits are determined by the `feat` type, or any other type
that has been configured with the semver type of `minor`. See
[commit_types](https://nrwldev.github.io/changelog-gen/configuration/#commit_types)
for details on custom type configuration.

### Patch

All other commit types are treated as `patch` releases.

## Typical release flow

The default versioning parser is
`(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)`, with the matching serialiser
`{major}.{minor}.{patch}`. This will support the typical semver use case of
`X.Y.Z` version strings.

## Prerelease flows

If you want to support a pre-release flow, configure a parser, suitable
serialisers, and any custom components (non incrementing integers).

```toml
[tool.changelog_gen]
current_version = "0.0.0"
pre_release = true
parser = '''(?x)
    (?P<major>0|[1-9]\d*)\.
    (?P<minor>0|[1-9]\d*)\.
    (?P<patch>0|[1-9]\d*)
    (?:
        (?P<pre_l>[a-zA-Z-]+)         # pre-release label
        (?P<pre_n>0|[1-9]\d*)         # pre-release version number
    )?                                # pre-release section is optional
'''
serialisers = [
    "{major}.{minor}.{patch}-{pre_l}{pre_n}",
    "{major}.{minor}.{patch}",
]

parts.pre_l = ["dev", "rc"]
```

In the above example on creating a major/minor/patch release, the `pre_l`
component will increment to the initial value `dev`, and `pre_n` will be 0.

* `0.0.0`
* `0.0.0      → 0.0.1-dev0  [changelog generate]`
* `0.0.1-dev0 → 0.0.1-dev1  [changelog generate --version-part pre_n]`
* `0.0.1-dev1 → 0.0.1-rc0   [changelog generate --version-part pre_l]`
* `0.0.1-rc   → 0.0.1       [changelog generate --version-part pre_l]`

When the release component reaches the end of the configured component parts,
the optional components will be dropped.

Prerelease flows are triggered on `major`, `minor`, and `patch`
releases. If you only wanted them to occur on major releases, use the
[pre_release_components](https://nrwldev.github.io/changelog-gen/configuration/#pre_release_components)
configuration.

They are also disabled by default, so configure
`[tool.changelog_gen.pre_release]` or use `--prerelease` override on the
command line.

## Strict validation

By default, parsers and serialisers that do not strictly adhere to SemVer 2.0.0 are
supported, but if you wish, strict validation can be enforced. If
[enabled](https://nrwldev.github.io/changelog-gen/configuration/#strict)
the tool will error if an incorrect parser, serialiser or component
configuration is provided.
