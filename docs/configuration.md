# Configuration

..TODO
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

## Configuration file -- Global configuration

General configuration is grouped in a `[changelog_gen]` section.

### `commit`
  _**[optional]**_<br />
  **default**: True

  Commit changes to the changelog (and configured files) after writing.

  Also available as `--commit/--no-commit` (e.g. `changelog generate --commit`)

### `tag`
  _**[optional]**_<br />
  **default**: True

  Tag the committed changes with the new version.

  Also available as `--tag/--no-tag` (e.g. `changelog generate --tag`)

### `release`
  _**[optional]**_<br />
  **default**: True

  Modify version strings in configured files.

  Also available as `--release/--no-release` (e.g. `changelog generate --release`)

### `allow_dirty`
  _**[optional]**_<br />
  **default**: False

  Don't abort if the current branch contains uncommitted changes

  Also available as `--allow-dirty` (e.g. `changelog generate --allow-dirty`)

### `reject_empty`
  _**[optional]**_<br />
  **default**: False

  Abort if there are no release notes to add to the change log.

  Also available as `--reject-empty` (e.g. `changelog generate --reject-empty`)

### `issue_link`
  _**[optional]**_<br />
  **default**: None

  Create links in the CHANGELOG to the originating issue. A url that contains
  an `issue_ref` placeholder for replacement.

  Example:

```toml
[tool.changelog_gen]
issue_link = "http://github.com/NRWLDev/changelog-gen/issues/::issue_ref::"
```

### `commit_link`
  _**[optional]**_<br />
  **default**: None

  Create links in the CHANGELOG to the originating commit. A url that contains
  a `::commit_hash::` placeholder for replacement.

  Example:

```toml
[tool.changelog_gen]
commit_link = "http://github.com/NRWLDev/changelog-gen/commit/::commit_hash::"
```

### `version_string`
  _**[optional]**_<br />
  **default**: `v{new_version}`

  Format for the version tag, this will be passed into changelog, commit
  messages, and any post processing.

  Example:

```toml
[tool.changelog_gen]
version_string = "{new_version}"
```

### `date_format`
  _**[optional]**_<br />
  **default**: None

  Add a date on the version line, use [strftime and strptime format
  codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).
  The format string can include any character, a space is included between the
  version tag and the date tag.

  Also available in cli as `--date-format` (e.g. `--date-format '%Y-%m-%d'`).

  Example:

```toml
[tool.changelog_gen]
date_format = "on %Y-%m-%d"
```

### `allowed_branches`
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

### `commit_types`
  _**[optional]**_<br />
  **default**: None

  Provide new commit types and which headers and semver component in the
  changelog they should map to, default semver is `patch`. Partial overrides to
  the built in commit types can also be provided.

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

    See `changelog config` for the existing configuration.

## Versioning

Versioning configuration is very similar to
[bump-my-version](https://github.com/callowayproject/bump-my-version?tab=readme-ov-file#semantic-versioning-example),
but with a few simplifications.

The default configuration will support the typical semver use case of `X.Y.Z`
version strings.

### `current_version`
  _**[optional]**_<br />
  **default**: None

The minimum required configuration to manage versions is the current version,
which can be moved directly from `[tool.bumpversion]`

If not provided, `bumpversion` will be used to generate releases.

```toml
[tool.changelog_gen]
current_version = "1.2.3"
```

### `files`
  _**[optional]**_<br />
  **default**: None

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

### `parser`
  _**[optional]**_<br />
  **default**: `(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)`

The parser is used to extract the existing semver components from the current
version configuration.

If you want to support a pre-release flow, configure a parser a new parser for the custom components you require.

Example:

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
```

### `serialisers`
  _**[optional]**_<br />
  **default**: `["{major}.{minor}.{patch}"]`

The serialisers should be defined from most greedy to least in the case where
there are optional components.

Example:

```toml
[tool.changelog_gen]
serialisers = [
    "{major}.{minor}.{patch}-{pre_l}{pre_n}",
    "{major}.{minor}.{patch}",
]
```

### `parts`

Where custom components have been defined, if a component uses non integer
values the valid values can be defined.

When the release component reaches the end of the configured component parts,
the optional components will be dropped.

Example:

```
[tool.changelog_gen.parts]
pre_l = ["dev", "rc"]
```

## Post processing

### `post_process`
  _**[optional]**_<br />
  **default**: None

  Configure a REST API to contact when a release is made

  See example on below Jira configuration information.

#### `post_process.url`
  _**[required]**_<br />
  **default**: None<br />
  The url to contact.
  Can have the placeholders `::issue_ref::` and `::version::``.

#### `post_process.verb`
  _**[optional]**_<br />
  **default**: POST<br />
  HTTP method to use.

#### `post_process.body`
  _**[optional]**_<br />
  **default**: `{"body": "Released on ::version::"}`<br />
  The text to send to the API.
  Can have the placeholders `::issue_ref::` and `::version::`.

#### `post_process.headers`
  _**[optional]**_<br />
  **default**: None<br />
  Headers dictionary to inject into http requests.

#### `post_process.auth_type`
  _**[optional]**_<br />
  **default**: basic<br />
  Auth type to use for post process requests, supported options are `basic` and `bearer`.

#### `post_process.auth_env`
  _**[optional]**_<br />
  **default**: None<br />
  Name of the environment variable to use to extract the basic auth information to contact the API.

  * For basic auth the content of the variable should be `{user}:{api key}`.
  * For bearer auth the content of the variable should be `{api key}`.

### Post process example
  Example to post to JIRA:

```toml
[tool.changelog_gen.post_process]
url = "https://your-domain.atlassian.net/rest/api/2/issue/ISSUE-::issue_ref::/comment"
verb = "POST"
body = '{"body": "Released on ::version::"}'
auth_env = "JIRA_AUTH"
headers."content-type" = "application/json"
```

  This assumes an environment variable `JIRA_AUTH` with the content
  `user@domain.com:{api_key}`.  See
  [manage-api-tokens-for-your-atlassian-account](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
  to generate a key.

  For simpler testing of post process flows, the url and auth env can be
  provided on the command line as `--post-process-url` and
  `--post-process-auth-env` (e.g. `changelog generate --post-process-url
  'http://my-api-url.domain/comment/::issue_ref::' --post-process-auth-env
  MY_API_AUTH`)
