# Configuration

Of the command line arguments, most of them can be configured in `setup.cfg` or `pyproject.toml` to remove
the need to pass them in every time.

Example `pyproject.toml`:

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

NOTE: setup.cfg is being deprecated, use `changelog migrate` to generate valid
toml from existing setup.cfg file.

Example `setup.cfg`:

```ini
[changelog_gen]
commit = true
release = true
allow_dirty = false
```

## Configuration file -- Global configuration

General configuration is grouped in a `[changelog_gen]` section.

### `commit = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Commit changes to the changelog after writing.

  Also available as `--commit` (e.g. `changelog generate --commit`)

### `release = (True | False)`
  _**[optional]**_<br />
  **default**: False

  Use bumpversion to tag the release

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

  When using in `setup.cfg` be sure to protect the `%` signs by using `%%` and
  be mindful about spacing as the string is taken straight from the `=` sign.

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

### `sections =`
  _**[Deprecated]**_<br />
  _**[optional]**_<br />
  **default**:

```toml
feat = "Features and Improvements"
fix = "Bug fixes"
docs = "Documentation"
misc = "Miscellaneous"
```

  Define custom headers or new sections/headers, new sections will require a
  matching section_mapping configuration.

  This configuration has been deprecated, use `commit_types` instead.

  Example:

```toml
[tool.changelog_gen.sections]
feat = "New Features"
change = "Changes"
remove = "Removals"
fix = "Bugfixes"
```

### `section_mapping =`
  _**[Deprecated]**_<br />
  _**[optional]**_<br />
  **default**:

```toml
bug = "fix"
chore = "misc"
ci = "misc"
docs = "docs"
perf = "misc"
refactor = "misc"
revert = "misc"
style = "misc"
test = "misc"
```

  Configure additional supported commit types to supported changelog sections.

  This configuration has been deprecated, use `commit_types` instead.

  Example:

```toml
[tool.changelog_gen.section_mapping]
test = "fix"
bugfix = "fix"
docs = "fix"
new = "feat"
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

  If using setup.cfg, provide a json string representation of the headers.

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
