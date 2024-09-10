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

* `type` is used to determining the semantic version related to the change.
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

Parsing additional/custom footers is supported with
[footer_parsers](https://nrwldev.github.io/changelog-gen/configuration/#footer_parsers).

### Github support

Github makes use of `closes #<issue_ref>` to close an issue when merged, this
footer, along with other custom github footers, can be used to extract the
`issue_ref`.  Github also inserts `(#<pull_ref)` into merge request titles, if
you make use of the title/description when merging, this can be stripped out,
and optionally stored in a `PR` footer.

See [github](https://nrwldev.github.io/changelog-gen/configuration/#github)
configuration for details.

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

## Extracting information and using it

To parse information from custom footers check out
[footer_parsers](https://nrwldev.github.io/changelog-gen/configuration/#footer_parsers).

By supplying custom regexes that split a footer into the
`[footer][separator][footer_value]` this information can be extracted later on
and used to generate links, or to populate the post process url/body.

### Information extraction

Once footers have been parsed, their information can be extracted to support templating links etc.

Custom
[extractors](https://nrwldev.github.io/changelog-gen/configuration/#extractors)
can be defined using named group regexes, for example to extract issue_refs
from the footer `Refs: #1, #2, #3` an extractor `#(?P<issue_ref>\d+),?`, would
result in the extracted information `{"issue_ref": ["1", "2", "3"]}`.

Multiple footers can be extracted using the same group name, and the data will
be concatenated together (rather than overwritten) from subsequent extractors.

### Links

Once information has been extracted from parsed footers, it can be used to
generate links to include in the changelog. See
[link_generators](https://nrwldev.github.io/changelog-gen/configuration/#link_generators)
for information on configuring link generators.

In previous releases, `changelog-gen` only supported `issue_link` and
`commit_link` configuration. These have been deprecated in favour of
link_generators. The same behaviour can be recreated using a link generator.

The following toml will generate a link for each extracted issue_ref, and will
generate a link using the short_hash and full commit_hash of the raw change
object.

```toml
[[tool.changelog_gen.link_generators]]
source = "issue_ref"
link = "https://github.com/NRWLDev/changelog-gen/issues/{0}"

[[tool.changelog_gen.link_generators]]
source = "__change__"
text = "{0.short_hash}"
link = "https://github.com/NRWLDev/changelog-gen/commit/{0.commit_hash}"
```

To generate a link for a PR, using the PR footer from the github helpers.

```toml
[[tool.changelog_gen.extractors]]
footer = "PR"
pattern = '#(?P<pull_ref>\d+)'

[[tool.changelog_gen.link_generators]]
source = "pr"
link = "https://github.com/NRWLDev/changelog-gen/pulls/{0}"
```
