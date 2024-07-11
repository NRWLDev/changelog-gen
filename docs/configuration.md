# Configuration

Of the command line arguments, most of them can be configured in `pyproject.toml` to remove
the need to pass them in every time.

Example:

```toml
[tool.changelog_gen]
commit = true
release = true
allow_dirty = false

[tool.changelog_gen.post_process]
  url = "https://your-domain.atlassian.net/rest/api/2/issue/ISSUE-::issue_ref::/comment"
  verb = "POST"
  body = '{"body": "Released on v::version::"}'
  auth_env = "JIRA_AUTH"
```

## Versioning

`changelog-gen` is bringing version management "in house", and deprecating
subprocess calls to `bump-my-version`.

The configuration is very similar to
[bump-my-version](https://github.com/callowayproject/bump-my-version?tab=readme-ov-file#semantic-versioning-example),
but with a few simplifications.

The minimum required configuration to manage versions is the current version,
which can be moved directly from `[tool.bumpversion]`

```toml
[tool.changelog_gen]
current_version = "1.2.3"
```

If multiple files have the current version string in them, they can be
configured for replacement.

Where the version string can safely be replaced with the default pattern
`{version}`, use:

```
[[tool.changelog_gen.files]]
filename = "README.md"
```

For files that might contain other version strings that could match and
shouldn't be updated, a search/replace pattern can be configured.

```
[[tool.changelog_gen.files]]
filename = "pyproject.toml"
pattern = 'version = "{version}"'
```

### Version patterns

The default versioning parser is
`(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)`, with the matching serialiser
`{major}.{minor}.{patch}`. This will support the typical semver use case of
`X.Y.Z` version strings.

If you want to support a pre-release flow, configure a parser, suitable
serialisers, and any custom components (non incrementing integers).

```toml
[tool.changelog_gen]
parser = '''(?x)
    (?P<major>0|[1-9]\d*)\.
    (?P<minor>0|[1-9]\d*)\.
    (?P<patch>0|[1-9]\d*)
    (?:
        (?P<pre_l>[a-zA-Z-]+)         # pre-release label
        (?P<pre_n>0|[1-9]\d*)         # pre-release version number
    )?                                # pre-release section is optional
'''
serializers = [
    "{major}.{minor}.{patch}-{pre_l}{pre_n}",
    "{major}.{minor}.{patch}",
]

[tool.changelog_gen.parts]
pre_l = ["dev", "rc"]
```

In the above example on creating a major/minor/patch release, the `pre_l`
component will increment to the initial value `dev`, and `pre_n` will be 0.

* `0.0.0`
* `0.0.0      → 0.0.1-dev0`  [changelog generate]
* `0.0.1-dev0 → 0.0.1-dev1`  [changelog generate --version-part pre_n]
* `0.0.1-dev1 → 0.0.1-rc0`   [changelog generate --version-part pre_l]
* `0.0.1-rc   → 0.0.1`       [changelog generate --version-part pre_l]

When the release component reaches the end of the configured component parts,
the optional components will be dropped.

## Configuration file -- Global configuration

General configuration is grouped in a `[changelog_gen]` section.

### `commit = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Commit changes to the changelog after writing.

  Also available as `--commit` (e.g. `changelog generate --commit`)

### `tag = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Tag the committed changes with the new version.

  Also available as `--tag` (e.g. `changelog generate --tag`)

### `release = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Modify version strings in files with bumpversion.

  Also available as `--release` (e.g. `changelog generate --release`)

### `allow_dirty = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Don't abort if the current branch contains uncommitted changes

  Also available as `--allow-dirty` (e.g. `changelog generate --allow-dirty`)

### `reject_empty = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Abort if there are no release notes to add to the change log.

  Also available as `--reject-empty` (e.g. `changelog generate --reject-empty`)

### `issue_link =`
  _**[optional]**_<br />
  **default**: None

  Create links in the CHANGELOG to the originating issue. A url that contains
  an `issue_ref` placeholder for replacement.

  Example:

```toml
[tool.changelog_gen]
issue_link = "http://github.com/NRWLDev/changelog-gen/issues/::issue_ref::"
```

### `commit_link =`
  _**[optional]**_<br />
  **default**: None

  Create links in the CHANGELOG to the originating commit. A url that contains
  a `::commit_hash::` placeholder for replacement.

  Example:

```toml
[tool.changelog_gen]
commit_link = "http://github.com/NRWLDev/changelog-gen/commit/::commit_hash::"
```

### `version_string =`
  _**[optional]**_<br />
  **default**: `v{new_version}`

  Format for the version tag, this will be passed into changelog, commit
  messages, and any post processing.

  Example:

```toml
[tool.changelog_gen]
version_string = "{new_version}"
```

### `date_format =`
  _**[optional]**_<br />
  **default**: None

  Add a date on the version line, use [strftime and strptime format
  codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).
  The format string can include any character, a space is included between the
  version tag and the date tag.

  Also available as `--date-format` (e.g. `--date-format '%Y-%m-%d'`).

  Example:

```toml
[tool.changelog_gen]
date_format = "on %Y-%m-%d"
```

### `allowed_branches =`
  _**[optional]**_<br />
  **default**: None

  Prevent changelog being generated if the current branch is not in the
  supplied list. By default all branches are allowed.

  Example:

```toml
[tool.changelog_gen]
allowed_branches = [
  "main",
  "develop",
]
```

### `commit_types = `
  _**[optional]**_<br />
  **default**:

```toml
feat.header = "Features and Improvements"
feat.semver = "minor"
fix.header = "Bug fixes"
fix.semver = "patch"
docs.header = "Documentation"
docs.semver = "patch"
bug.header = "Bug fixes"
bug.semver = "patch"
chore.header = "Miscellaneous"
chore.semver = "patch"
ci.header = "Miscellaneous"
ci.semver = "patch"
perf.header = "Miscellaneous"
perf.semver = "patch"
refactor.header = "Miscellaneous"
refactor.semver = "patch"
revert.header = "Miscellaneous"
revert.semver = "patch"
style.header = "Miscellaneous"
style.semver = "patch"
test.header = "Miscellaneous"
test.semver = "patch"
```

  Define commit types and which headers and semver in the changelog they should map to, default semver is `patch`.

  Example:

```toml
[tool.changelog_gen.commit_types]
feat.header = "New Features"
feat.semver = "minor"
change.header = "Changes"
remove.header = "Removals"
remove.semver = "minor"
fix.header = "Bugfixes"
```

### `post_process =`
  _**[optional]**_<br />
  **default**: None

  Configure a REST API to contact when a release is made

  See example on Jira configuration information.

 `.url =`<br />
  _**[required]**_<br />
  **default**: None<br />
  The url to contact.
  Can have the placeholders `::issue_ref::` and `::version::``.

  `.verb =`<br />
  _**[optional]**_<br />
  **default**: POST<br />
  HTTP method to use.

  `.body =`<br />
  _**[optional]**_<br />
  **default**: `{"body": "Released on ::version::"}`<br />
  The text to send to the API.
  Can have the placeholders `::issue_ref::` and `::version::`.

  `.headers =`<br />
  _**[optional]**_<br />
  **default**: None<br />
  Headers dictionary to inject into http requests.

  `.auth_type =`<br />
  _**[optional]**_<br />
  **default**: basic<br />
  Auth type to use for post process requests, supported options are `basic` and `bearer`.

  `.auth_env =`<br />
  _**[optional]**_<br />
  **default**: None<br />
  Name of the environment variable to use to extract the basic auth information to contact the API.

  * For basic auth the content of the variable should be `{user}:{api key}`.
  * For bearer auth the content of the variable should be `{api key}`.

  Example to post to JIRA:

```toml
[tool.changelog_gen.post_process]
url = "https://your-domain.atlassian.net/rest/api/2/issue/ISSUE-::issue_ref::/comment"
verb = "POST"
body = '{"body": "Released on ::version::"}'
auth_env = "JIRA_AUTH"
headers."content-type" = "application/json"
```
  This assumes an environment variable `JIRA_AUTH` with the content `user@domain.com:{api_key}`.
  See
  [manage-api-tokens-for-your-atlassian-account](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
  to generate a key.

  Also partially available as `--post-process-url` and `--post-process-auth-env` (e.g. `changelog generate --post-process-url 'http://my-api-url.domain/comment/::issue_ref::' --post-process-auth-env MY_API_AUTH`)

## Pre-release flows

If your versioning uses prerelease version parts, after a major/minor/patch update creates e.g. `v0.0.1rc0`, use
`--version-part=<part>` to trigger release flows, based on your configuration.

```bash
$ changelog generate --version-part build
... v0.0.1rc1
```
