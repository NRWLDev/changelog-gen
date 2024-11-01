# Configuration

General configuration is grouped in the `[tool.changelog_gen]` section of pyproject.toml.

## Simple configuration

```toml
[tool.changelog_gen]
current_version = "1.2.3"
reject_empty = true
allowed_branches = [
    "main",
]

[[tool.changelog_gen.files]]
filename = "README.md"
```

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

### `interactive`
  _**[optional]**_<br />
  **default**: True

  Open proposed changes in an editor before writing to changelog.

  Also available as `--interactive/--no-interactive` (e.g. `changelog generate --interactive`)

### `allow_dirty`
  _**[optional]**_<br />
  **default**: False

  Don't abort if the current branch contains uncommitted changes

  Also available as `--allow-dirty` (e.g. `changelog generate --allow-dirty`)

### `allow_missing`
  _**[optional]**_<br />
  **default**: False

  Don't abort if the local and remote branches are out of sync.

  Also available as `--allow-missing` (e.g. `changelog generate --allow-missing`)

### `reject_empty`
  _**[optional]**_<br />
  **default**: False

  Abort if there are no release notes to add to the change log.

  Also available as `--reject-empty` (e.g. `changelog generate --reject-empty`)

### `statistics`
  _**[optional]**_<br />
  **default**: False

  Output commit message statistics summary to screen after changelog generation.

  Also available as `--statistics` (e.g. `changelog generate --statistics`)

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

### `footer_parsers`
  _**[optional]**_<br />
  **default**: None

  Define new footer parsers, or override builtin footer parsers (Authors,
  Refs). Footer parsers accepts a list of regexes to parse a footer and return
  a match with the footer, the separator, and the footer value.

  Example:
```toml
[tool.changelog_gen]
footer_parsers = [
    r"(Refs)(: )(#?[\w-]+)",
    r"(closes)( )(#[\w-]+)",
    r"(Authors)(: )(.*)",
]
```

### `extractors`
  _**[optional]**_<br />
  **default**: None

  Define parsers to extract information from footers and store them on the
  change object. Extractors should used named groups in regex expressions, this
  groups are the key to retrieve the information later in link generation or
  post processing. Extractors find all matches in a footer, so will be a
  list of all matched values. `Refs: 1, 2` will be parsed as
  `{"issue_ref": ["1", "2"]}` for example.

  The footer configuration can be a single footer, or a list of related footers.

  Example:

```toml
[[tool.changelog_gen.extractors]]
footer = "Refs"
pattern = '(?P<issue_ref>\d+)'

[[tool.changelog_gen.extractors]]
footer = ["closes", "fixes"]
pattern = '#(?P<issue_ref>\d+)'
```

### `link_generators`
  _**[optional]**_<br />
  **default**: None

  Make use of extracted information to generate links to different content.
  Define an extraction source, provide a regex pattern to extract
  information from the footer, and define the link format, optionally define
  the link text format. Link text will default to the extracted information.

  A special source `__change__` is provided to generate links using information
  directly from the change object (namely commit hashes).

  Where an extraction contains multiple values, a link for each match will be
  created. This allows adding links to multiple authors from the Author footer
  for example.

  Example:

```toml
[[tool.changelog_gen.link_generators]]
source = "issue_ref"
link = "https://github.com/NRWLDev/changelog-gen/issues/{0}"

[[tool.changelog_gen.link_generators]]
source = "__change__"
link = "https://github.com/NRWLDev/changelog-gen/commit/{0.commit_hash}"
text = "{0.short_hash}"
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

  Provide new commit types to support, along with the header to group them under
  All custom types will default to `patch` semver as well, to configure
  additional types to be treated as `minor` see
  [minor_regex](https://nrwldev.github.io/changelog-gen/configuration/#minor_regex)

  Example:

```toml
[tool.changelog_gen]
commit_types = [
    {"type" = "feat", "header" = "New Features"},
    {"type" = "change", "header" = "Changes"},
    {"type" = "remove", "header" = "Removals"},
    {"type" = "fix", "header" = "Bugfixes"},
]
```

    Run `changelog config` to see the existing configuration.

### `minor_regex`
  _**[optional]**_<br />
  **default**: None

  Provide a new type match regex for which types should be treated as features
  and trigger a minor bump.

  Example:

```toml
[tool.changelog_gen]
minor_regex = "feat|remove"
```

    See `changelog config` for the existing configuration.

### `hooks`
  _**[optional]**_<br />
  **default**: None

  Run additional hooks when generating a release, this allows regenerating
  automated documentation during release process, for example.

  Example:

```toml
[tool.changelog_gen]
hooks = [
  "path.to.module:hook_function",
]
```

### `custom`
  _**[optional]**_<br />
  **default**: None

  Arbitrary configuration that can be used in hooks.

  Example:

```toml
[tool.changelog_gen.custom]
key = "value"
a_list = ["key", "key2"]
```

### `change_template`
  _**[optional]**_<br />
  **default**: None

  Customise how changelog entries are formatted, uses
  [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) formatting.

  The template will provided with the change object and can render all
  extracted information as desired. For readability the template can be split
  over multiple lines, it will be flattened before it is rendered to generate a
  single line entry.

  Example:

```toml
[tool.changelog_gen]
change_template = """
-{% if change.scope %} (`{{change.scope}}`){% endif %}
{% if change.breaking %} **Breaking**{% endif %}
 {{ change.description }}
{% for footer in change.footers %}{% if footer.footer == "Authors"%} {{footer.value}}{% endif %}{% endfor %}
{% for link in change.links %} [[{{ link.text }}]({{ link.link }})]{% endfor %}
"""
```

  This can be tested using an example commit with the command
```bash
$ changelog test [COMMITHASH] --template change
```

### `release_template`
  _**[optional]**_<br />
  **default**: None

  Customise how release entries are formatted, uses
  [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) formatting.

  The template will provided with the release version string, and a dictionary
  of headers and related changes, changes have a `rendered` property containing the
  output of the configured `change_template` for that change.

  Example:

```toml
"""
[tool.changelog_gen]
release_template = """## {{ version_string }}

{% for header, changes in group_changes.items() -%}
### {{ header }}

{% for change in changes -%}
{{change.rendered}}
{% endfor %}
{% endfor %}
"""
```

  This can be tested using an commits since a specific hash with the command
```bash
$ changelog test [COMMITHASH] --template release
```

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

### `pre_release`
  _**[optional]**_<br />
  **default**: false

  Allow pre-release flows.

  Also available as `--pre-release/--no-pre-release` (e.g. `changelog generate --pre-release`)

### `pre_release_components`
  _**[optional]**_<br />
  **default**: None

  Configure which components trigger a pre-release flow.

  Example:

```
[tool.changelog_gen]
pre_release_components = ["major", "minor"]
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
  _**[optional]**_<br />
  **default**: None

  Where custom components have been defined, if a component uses non integer
  values the valid values can be defined.

  When the release component reaches the end of the configured component parts,
  the optional components will be dropped.

  Example:

```
[tool.changelog_gen.parts]
pre_l = ["dev", "rc"]
```

### `strict`
  _**[optional]**_<br />
  **default**: False

  Enforce strict rules based on SemVer 2.0.0 and error if non conforming parser or
  serialisers are configured.


## Github

### `strip_pr_from_description`
  _**[optional]**_<br />
  **default**: False

  Strip the `(#\d+)` from the end of github PR commit descriptions.

  Example:

```toml
[tool.changelog_gen.github]
strip_pr_from_description = true
```

### `extract_pr_from_description`
  _**[optional]**_<br />
  **default**: False

  Extract the `(#\d+)` from the end of github PR commit descriptions, and track
  it as a footer for later extraction and link generation. Creates a `PR` footer entry.

  Example:

```toml
[tool.changelog_gen.github]
extract_pr_from_description = true
```

### `extract_common_footers`
  _**[optional]**_<br />
  **default**: False

  Extract supported keyword footers from github commits, `closes #1` etc.

  Supported footers can be found
  [here](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue).

  Example:

```toml
[tool.changelog_gen.github]
extract_common_footers = true
```

## Post processing

### `post_process`
  _**[optional]**_<br />
  **default**: None

  Configure a REST API to contact when a release is made

  See example on below Jira configuration information.

#### `post_process.link_generator`
  _**[required]**_<br />
  **default**: None<br />
  The url to contact.
  Can have the placeholders `::issue_ref::` and `::version::``.

#### `post_process.verb`
  _**[optional]**_<br />
  **default**: POST<br />
  HTTP method to use.

#### `post_process.body_template`
  _**[optional]**_<br />
  **default**: `{"body": "Released on {{ version }}"}`<br />
  The text to send to the API.
  Can have the placeholders
  * `source` (usually the issue ref from the extracted information)
  * `version` the version being released
  * Any extracted key from defined extractors that had a match.

#### `post_process.headers`
  _**[optional]**_<br />
  **default**: None<br />
  Headers dictionary to inject into http requests.

#### `post_process.auth_type`
  _**[optional]**_<br />
  **default**: basic<br />
  Auth type to use for post process requests, supported options are `basic`, `aws4`, and `bearer`.

#### `post_process.auth_env`
  _**[optional]**_<br />
  **default**: None<br />
  Name of the environment variable to use to extract the basic auth information to contact the API.

  * For basic auth the content of the variable should be `{user}:{api key}`.
  * For bearer auth the content of the variable should be `{api key}`.
  * For signed aws4 auth the content of the variable should be `{access_key_id}:{secret_access_key}:{service_name}:{region}`.

### Post process example
  Example to post to JIRA:

```toml
[tool.changelog_gen.post_process]
link_generator.source = "issue_ref"
link_generator.link = "https://your-domain.atlassian.net/rest/api/2/issue/ISSUE-{0}/comment"
verb = "POST"
body = '{"body": "Released on {{ version }}"}'
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
