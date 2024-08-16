# Conventional commits

For full details on conventional commits, check out [conventional
commit](https://www.conventionalcommits.org/en/v1.0.0/).

## Commit messages

At the simplest level they can be achieved in a single line i.e.

```bash
$ git commit -m 'fix: Handle incorrect user input.'
```

Or with a multiline commit message with additional information in the body
and the footers, the body is ignored for the purposes of changelog generation,
but the footers are taken into account.

```
<type>[(optional scope)][!]: <description>

[optional body]

[optional footer(s)]
```

* `type` is used to determening the semantic version related to the change.
* `!` in the type, or `BREAKING CHANGE:` in the footer denotes a `major` release.
* `scope` is included in the changelog message if provided.
* `description` allows typical `[a-zA-Z ]` sentences, as well as `[.,/]`
  punctuation, and ``[`]`` for highlighting words. It is also the main
  information used in the changelog entry.

## Footers

Optional footers that are parsed by `changelog-gen` are:

* `BREAKING CHANGE:[ details]`
* `Refs: [#]<issue_ref>`
* `Authors: (<author>, ...)`
* `closes #<issue_ref>`

Note: The `closes #<issue_ref>` footed is included as a convenience for anyone
using github and using PR title/description for the commit message to remove
the need to also add a `Refs:` footer.

## Breaking changes

If an `!` is present in the commit type, or the `BREAKING CHANGE` footer is
present, a major release will be triggered, except in the case of `0.x.y` where
a breaking change will trigger a minor release (as detailed in semantic
versioning).

## Include all

Getting started with conventional commits can take some dedication, and its
easy to let some commits slip through the cracks. When generating changelogs
the `--include-all` flag is available to pick up all commits, even those that
don't fit the conventional commit format. All non conventional commits will be
included under a `Miscellaneous` heading. Combined with the `--interactive`
flag commits can be included under the correct headings and/or excluded
completely.
