# Usage

`changelog` currently supports generating from commit logs using [Conventional
Commits](https://www.conventionalcommits.org/en/v1.0.0/), as well as reading
changes from a `release_notes` folder.

NOTE: `release_notes` support will be dropped in a future version, migration to
conventional commits is recommended.

See [Configuration](/changelog-gen/configuration) below for default commit type configuration
and how to customize them.

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

## Release Notes

Files in the folder should use the format `{issue_number}.{type}`.

The contents of each file is used to populate the changelog file. If the type
ends with a `!` it denotes a breaking change has been made, this will lead to a
major release being suggested.

```bash
$ ls release_notes
  4.fix  7.fix

$ changelog generate

## v0.2.1

### Bug fixes

- Raise errors from internal classes, don't use click.echo() [#4]
- Update changelog line format to include issue number at the end. [#7]

Write CHANGELOG for suggested version 0.2.1 [y/N]: y
```