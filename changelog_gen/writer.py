"""Writer implementations for different changelog extensions."""

from __future__ import annotations

import typing as t
from collections import defaultdict
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile

from changelog_gen.util import timer

if t.TYPE_CHECKING:
    from changelog_gen.context import Context
    from changelog_gen.extractor import Change


class Extension(Enum):
    """Supported changelog file extensions."""

    MD = "md"
    RST = "rst"


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
        self.issue_link = context.config.issue_link
        self.commit_link = context.config.commit_link
        self.pull_link = context.config.pull_link

    @timer
    def add_version(self: t.Self, version: str) -> None:
        """Add a version string to changelog file."""
        self._add_version(version)

    @timer
    def _add_version(self: t.Self, version: str) -> None:
        raise NotImplementedError

    @timer
    def consume(self: t.Self, type_headers: dict[str, str], changes: list[Change]) -> None:
        """Process sections and generate changelog file entries."""
        grouped_changes = defaultdict(list)
        for change in changes:
            grouped_changes[change.header].append(change)

        for header in type_headers.values():
            if header not in grouped_changes:
                continue
            # Remove processed headers to prevent rendering duplicate type -> header mappings
            changes_ = grouped_changes.pop(header)
            self.add_section(header, changes_)

    @timer
    def add_section(self: t.Self, header: str, changes: list[Change]) -> None:
        """Add a section to changelog file."""
        self._add_section_header(header)
        for change in sorted(changes):
            description = f"{change.scope} {change.description}" if change.scope else change.description
            description = f"{self.bold_string('Breaking:')} {description}" if change.breaking else description
            description = f"{description} {change.authors}" if change.authors else description

            self._add_section_line(
                description,
                change,
            )
        self._post_section()

    @timer
    def bold_string(self: t.Self, string: str) -> str:
        """Render a string as bold."""
        return f"**{string.strip()}**"

    @timer
    def _add_section_header(self: t.Self, header: str) -> None:
        raise NotImplementedError

    @timer
    def _add_section_line(self: t.Self, description: str, change: Change) -> None:
        raise NotImplementedError

    @timer
    def _post_section(self: t.Self) -> None:
        pass

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
    def _add_version(self: t.Self, version: str) -> None:
        self.content.extend([f"## {version}", ""])

    @timer
    def _add_section_header(self: t.Self, header: str) -> None:
        self.content.extend([f"### {header}", ""])

    @timer
    def _add_section_line(self: t.Self, description: str, change: Change) -> None:
        line = f"- {description}"

        for link in change.links:
            line = f"{line} [[{link.text}]({link.link})]"

        self.content.append(line)

    @timer
    def _post_section(self: t.Self) -> None:
        self.content.append("")


class RstWriter(BaseWriter):
    """RST writer implementation."""

    file_header_line_count = 3
    file_header = "=========\nChangelog\n=========\n"
    extension = Extension.RST

    @timer
    def __init__(self: t.Self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
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
    def _add_version(self: t.Self, version: str) -> None:
        self.content.extend([version, "=" * len(version), ""])

    @timer
    def _add_section_header(self: t.Self, header: str) -> None:
        self.content.extend([header, "-" * len(header), ""])

    @timer
    def _add_section_line(self: t.Self, description: str, change: Change) -> None:
        line = f"* {description}"

        for link in change.links:
            line = f"{line} [`{link.text}`_]"
            self._links[link.text] = link.link

        self.content.extend([line, ""])

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
    *,
    dry_run: bool = False,
) -> BaseWriter:
    """Generate a new writer based on the required extension."""
    changelog = Path(f"CHANGELOG.{extension.value}")

    if extension == Extension.MD:
        return MdWriter(changelog, context, dry_run=dry_run)
    if extension == Extension.RST:
        return RstWriter(changelog, context, dry_run=dry_run)

    msg = f'Changelog extension "{extension.value}" not supported.'
    raise ValueError(msg)
