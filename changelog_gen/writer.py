"""Writer implementations for different changelog extensions."""

from __future__ import annotations

import re
import typing as t
from collections import defaultdict
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

from jinja2 import BaseLoader, Environment

from changelog_gen.util import timer

if t.TYPE_CHECKING:
    from changelog_gen.context import Context
    from changelog_gen.extractor import Change


class Extension(Enum):
    """Supported changelog file extensions."""

    MD = "md"
    RST = "rst"


def regex_replace(value: str, target: str, replace: str) -> str:
    """Regex replace filter for jinja templates."""
    return re.sub(target, replace, value)


class BaseWriter:
    """Base implementation for a changelog file writer."""

    file_header_line_count = 0
    file_header = None
    extension = None

    @timer
    def __init__(
        self: t.Self,
        changelog: Path,
        context: Context,
        change_template: str | None = None,
        release_template: str | None = None,
        *,
        dry_run: bool = False,
    ) -> None:
        self.context = context
        self.existing = []
        self.changelog = changelog
        if self.changelog.exists():
            lines = changelog.read_text().split("\n")
            self.existing = lines[self.file_header_line_count + 1 :]
        self.content = []
        self.dry_run = dry_run
        self._change_template = change_template
        self._release_template = release_template

    @timer
    def _render_change(self: t.Self, change: Change) -> str:
        env = Environment(loader=BaseLoader())  # noqa: S701

        env.filters["regex_replace"] = regex_replace
        ctemplate = env.from_string(self._change_template.replace("\n", ""))

        return ctemplate.render(change=change)

    @timer
    def consume(self: t.Self, version_string: str, type_headers: dict[str, str], changes: list[Change]) -> None:
        """Process sections and generate changelog file entries."""
        grouped_changes = defaultdict(list)
        for change in changes:
            change.rendered = self._render_change(change)
            grouped_changes[change.header].append(change)

        ordered_group_changes = {}
        for header in type_headers.values():
            if header not in grouped_changes:
                continue
            # Remove processed headers to prevent rendering duplicate type -> header mappings
            changes_ = grouped_changes.pop(header)
            ordered_group_changes[header] = sorted(changes_)

        self._consume(version_string, ordered_group_changes)

    @timer
    def _consume(self: t.Self, version_string: str, group_changes: dict[str, list[Change]]) -> None:
        raise NotImplementedError

    @timer
    def __str__(self: t.Self) -> str:  # noqa: D105
        content = "\n".join(self.content)
        return f"\n\n{content}\n\n"

    @timer
    def write(self: t.Self) -> str:
        """Write file contents to destination."""
        self.content = [self.file_header, *self.content, *self.existing]
        self._write(self.content)

        return str(self.changelog)

    @timer
    def _write(self: t.Self, content: list[str]) -> None:
        if self.dry_run:
            self.context.warning("Would write to '%s'", self.changelog.name)
            with NamedTemporaryFile("wb") as output_file:
                output_file.write(("\n".join(content)).encode("utf-8"))
        else:
            self.context.warning("Writing to '%s'", self.changelog.name)
            self.changelog.write_text("\n".join(content))


class MdWriter(BaseWriter):
    """Markdown writer implementation."""

    file_header_line_count = 1
    file_header = "# Changelog\n"
    extension = Extension.MD

    @timer
    def __init__(self: t.Self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._change_template = (
            self._change_template
            or """
-{% if change.scope %} (`{{change.scope}}`){% endif %}
{% if change.breaking %} **Breaking**{% endif %}
 {{ change.description }}
{% for footer in change.footers %}{% if footer.footer == "Authors"%} {{footer.value}}{% endif %}{% endfor %}
{% for link in change.links %} [[{{ link.text }}]({{ link.link }})]{% endfor %}
"""
        )
        self._release_template = (
            self._release_template
            or """## {{ version_string }}

{% for header, changes in group_changes.items() -%}
### {{ header }}

{% for change in changes -%}
{{change.rendered}}
{% endfor %}
{% endfor %}
"""
        )

    @timer
    def _consume(self: t.Self, version_string: str, group_changes: dict[str, list[Change]]) -> None:
        env = Environment(loader=BaseLoader())  # noqa: S701

        env.filters["regex_replace"] = regex_replace
        rtemplate = env.from_string(self._release_template)

        content = rtemplate.render(group_changes=group_changes, version_string=version_string)
        self.content = content.split("\n")[:-1]


class RstWriter(BaseWriter):
    """RST writer implementation."""

    file_header_line_count = 3
    file_header = "=========\nChangelog\n=========\n"
    extension = Extension.RST

    @timer
    def __init__(self: t.Self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._change_template = (
            self._change_template
            or """
*{% if change.scope %} (`{{change.scope}}`){% endif %}
{% if change.breaking %} **Breaking**{% endif %}
 {{ change.description }}
{% for footer in change.footers %}{% if footer.footer == "Authors"%} {{footer.value}}{% endif %}{% endfor %}
{% for link in change.links %} [`{{ link.text }}`_]{% endfor %}
"""
        )
        self._release_template = (
            self._release_template
            or """{{ version_string }}
{{ "=" * version_string|length }}

{% for header, changes in group_changes.items() -%}
{{ header }}
{{ "-" * header|length }}

{% for change in changes -%}
{{change.rendered}}

{% endfor %}
{% endfor %}
"""
        )
        self._links = {}

    @timer
    def __str__(self: t.Self) -> str:  # noqa: D105
        content = "\n".join(self.content + self.links)
        return f"\n\n{content}\n\n"

    @property
    def links(self: t.Self) -> list[str]:
        """Generate RST supported links for inclusion in changelog."""
        return [f".. _`{ref}`: {link}" for ref, link in sorted(self._links.items())]

    @timer
    def _consume(self: t.Self, version_string: str, group_changes: dict[str, list[Change]]) -> None:
        env = Environment(loader=BaseLoader())  # noqa: S701

        env.filters["regex_replace"] = regex_replace
        rtemplate = env.from_string(self._release_template)

        content = rtemplate.render(group_changes=group_changes, version_string=version_string)
        self.content = content.split("\n")[:-2]

    @timer
    def _render_change(self: t.Self, change: Change) -> str:
        line = super()._render_change(change)

        for link in change.links:
            self._links[link.text] = link.link

        return line

    @timer
    def write(self: t.Self) -> str:
        """Write contents to destination."""
        self.content = [self.file_header, *self.content, *self.existing, *self.links]
        self._write(self.content)
        return str(self.changelog)


@timer
def new_writer(
    context: Context,
    extension: Extension,
    change_template: str | None = None,
    *,
    dry_run: bool = False,
) -> BaseWriter:
    """Generate a new writer based on the required extension."""
    changelog = Path(f"CHANGELOG.{extension.value}")

    if extension == Extension.MD:
        return MdWriter(changelog, context, dry_run=dry_run, change_template=change_template)
    if extension == Extension.RST:
        return RstWriter(changelog, context, dry_run=dry_run, change_template=change_template)

    msg = f'Changelog extension "{extension.value}" not supported.'
    raise ValueError(msg)
