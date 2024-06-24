# Usage

`changelog` currently supports generating from commit logs using [Conventional
Commits](https://www.conventionalcommits.org/en/v1.0.0/).

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

### Include all

Getting started with conventional commits can take some dedication, and its
easy to let some commits slip through the cracks. When generating changelogs
the `--include-all` flag is available to pick up all commits, even those that
don't fit the conventional commit format. All non conventional commits will be
included under a `Miscellaneous` heading. Combined with the `--interactive`
flag commits can be included under the correct headings and/or excluded
completely.
