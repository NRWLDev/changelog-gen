import pathlib
from unittest import mock

import pytest

from changelog_gen import writer
from changelog_gen.config import Config
from changelog_gen.context import Context
from changelog_gen.extractor import Change, Footer, Link


@pytest.fixture()
def changelog(tmp_path):
    p = tmp_path / "CHANGELOG"
    p.write_text("")
    return p


@pytest.fixture()
def changelog_md(tmp_path):
    p = tmp_path / "CHANGELOG.md"
    p.write_text("# Changelog\n")
    return p


@pytest.fixture()
def changelog_rst(tmp_path):
    p = tmp_path / "CHANGELOG.rst"
    p.write_text("=========\nChangelog\n=========\n")
    return p


@pytest.fixture()
def ctx():
    return Context(Config(current_version="0.0.0"))


@pytest.mark.parametrize(
    ("extension", "expected_cls"),
    [
        (writer.Extension.MD, writer.MdWriter),
        (writer.Extension.RST, writer.RstWriter),
    ],
)
def test_new_writer(extension, expected_cls, ctx):
    assert isinstance(writer.new_writer(ctx, extension), expected_cls)


def test_new_writer_raises_for_unsupported_extension(ctx):
    with pytest.raises(ValueError, match='Changelog extension "txt" not supported.'):
        writer.new_writer(ctx, mock.Mock(value="txt"))


class TestBaseWriter:
    def test_init(self, changelog, ctx):
        w = writer.BaseWriter(changelog, ctx)

        assert w.content == []
        assert w.dry_run is False

    def test_init_dry_run(self, changelog, ctx):
        w = writer.BaseWriter(changelog, ctx, dry_run=True)

        assert w.content == []
        assert w.dry_run is True

    def test_init_no_existing_entries(self, changelog, ctx):
        w = writer.BaseWriter(changelog, ctx)

        assert w.existing == []

    def test_init_stores_existing_changelog(self, changelog, ctx):
        changelog.write_text(
            """
## 0.0.1

### header

- line1
- line2
- line3
""",
        )
        w = writer.BaseWriter(changelog, ctx)

        assert w.existing == [
            "## 0.0.1",
            "",
            "### header",
            "",
            "- line1",
            "- line2",
            "- line3",
            "",
        ]

    def test_content_as_str(self, changelog, ctx):
        w = writer.BaseWriter(changelog, ctx)
        w.content = ["line1", "line2", "line3"]

        assert str(w) == "\n\nline1\nline2\nline3\n\n"

    def test_base_methods_not_implemented(self, changelog, ctx):
        w = writer.BaseWriter(changelog, ctx)

        with pytest.raises(NotImplementedError):
            w._add_section_header("header")

        with pytest.raises(NotImplementedError):
            w._add_section_line(Change("header", "issue_ref", "description", "fix"))

        with pytest.raises(NotImplementedError):
            w._add_version("0.0.0")

    def test_add_version(self, monkeypatch, changelog, ctx):
        monkeypatch.setattr(writer.BaseWriter, "_add_version", mock.Mock())
        w = writer.BaseWriter(changelog, ctx)

        w.add_version("0.0.0")

        assert w._add_version.call_args == mock.call("0.0.0")

    def test_add_section(self, monkeypatch, changelog, ctx):
        monkeypatch.setattr(writer.BaseWriter, "_add_section_header", mock.Mock())
        monkeypatch.setattr(writer.BaseWriter, "_add_section_line", mock.Mock())

        w = writer.BaseWriter(changelog, ctx)

        w.add_section(
            "header",
            [
                Change("header", "line1", "fix", breaking=True, footers=[Footer("Refs", ": ", "#1")]),
                Change(
                    "header",
                    "line2",
                    "fix",
                    footers=[Footer("Refs", ": ", "#2"), Footer("Authors", ": ", "(a, b)")],
                ),
                Change("header", "line3", "fix", scope="config", footers=[Footer("Refs", ": ", "#3")]),
            ],
        )

        assert w._add_section_header.call_args == mock.call("header")
        assert w._add_section_line.call_args_list == [
            mock.call(
                Change("header", "line1", "fix", breaking=True, footers=[Footer("Refs", ": ", "#1")]),
            ),
            mock.call(
                Change("header", "line3", "fix", scope="config", footers=[Footer("Refs", ": ", "#3")]),
            ),
            mock.call(
                Change(
                    "header",
                    "line2",
                    "fix",
                    footers=[Footer("Refs", ": ", "#2"), Footer("Authors", ": ", "(a, b)")],
                ),
            ),
        ]

    def test_add_section_sorting(self, monkeypatch, changelog, ctx):
        monkeypatch.setattr(writer.BaseWriter, "_add_section_header", mock.Mock())
        monkeypatch.setattr(writer.BaseWriter, "_add_section_line", mock.Mock())

        w = writer.BaseWriter(changelog, ctx)

        w.add_section(
            "header",
            [
                Change("header", "line3", "fix", breaking=True, footers=[Footer("Refs", ": ", "#3")]),
                Change(
                    "header",
                    "line2",
                    "fix",
                    footers=[Footer("Refs", ": ", "#2"), Footer("Authors", ": ", "(a, b)")],
                ),
                Change("header", "line1", "fix", scope="config", footers=[Footer("Refs", ": ", "#1")]),
            ],
        )

        assert w._add_section_header.call_args == mock.call("header")
        assert w._add_section_line.call_args_list == [
            mock.call(
                Change("header", "line3", "fix", breaking=True, footers=[Footer("Refs", ": ", "#3")]),
            ),
            mock.call(
                Change("header", "line1", "fix", scope="config", footers=[Footer("Refs", ": ", "#1")]),
            ),
            mock.call(
                Change(
                    "header",
                    "line2",
                    "fix",
                    footers=[Footer("Refs", ": ", "#2"), Footer("Authors", ": ", "(a, b)")],
                ),
            ),
        ]


class TestMdWriter:
    def test_init(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)

        assert w.content == []
        assert w.dry_run is False

    def test_init_dry_run(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx, dry_run=True)

        assert w.content == []
        assert w.dry_run is True

    def test_init_no_existing_entries(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)

        assert w.existing == []

    def test_init_stores_existing_changelog(self, changelog_md, ctx):
        changelog_md.write_text(
            """# Changelog

## 0.0.1

### header

- line1
- line2
- line3
""",
        )

        w = writer.MdWriter(changelog_md, ctx)

        assert w.existing == [
            "## 0.0.1",
            "",
            "### header",
            "",
            "- line1",
            "- line2",
            "- line3",
            "",
        ]

    def test_add_version(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)

        w._add_version("0.0.0")

        assert w.content == ["## 0.0.0", ""]

    def test_add_section_header(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)

        w._add_section_header("header")

        assert w.content == ["### header", ""]

    def test_add_section_line(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)

        w._add_section_line(Change("header", "line", "fix", footers=[Footer("Refs", ": ", "#1")]))

        assert w.content == ["- line"]

    def test_add_section_line_with_metadata(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)

        w._add_section_line(
            Change("header", "line", "fix", scope="config", breaking=True, footers=[Footer("Authors", ": ", "(a, b)")]),
        )

        assert w.content == ["- (`config`) **Breaking** line (a, b)"]

    def test_add_section_line_with_links(self, changelog_md):
        ctx = Context(Config(current_version="0.0.0"))
        w = writer.MdWriter(changelog_md, ctx)

        w._add_section_line(
            Change(
                "header",
                "line",
                "fix",
                links=[Link("#1", "http://url/issues/1"), Link("1234567", "http://url/commit/commit-hash")],
            ),
        )

        assert w.content == ["- line [[#1](http://url/issues/1)] [[1234567](http://url/commit/commit-hash)]"]

    def test_write_dry_run_doesnt_write_to_file(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx, dry_run=True)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            [
                Change("header", "line1", "fix", footers=[Footer("Refs", ": ", "#1")]),
                Change("header", "line2", "fix", footers=[Footer("Refs", ": ", "#2")]),
                Change("header", "line3", "fix", scope="config", footers=[Footer("Refs", ": ", "#3")]),
            ],
        )

        w.write()
        assert changelog_md.read_text() == """# Changelog\n"""

    def test_write(self, changelog_md, ctx):
        w = writer.MdWriter(changelog_md, ctx)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            [
                Change("header", "line1", "fix", footers=[Footer("Refs", ": ", "#1")]),
                Change("header", "line2", "fix", footers=[Footer("Refs", ": ", "#2")]),
                Change("header", "line3", "fix", scope="config", footers=[Footer("Refs", ": ", "#3")]),
            ],
        )

        w.write()
        assert (
            changelog_md.read_text()
            == """# Changelog

## 0.0.1

### header

- (`config`) line3
- line1
- line2
"""
        )

    def test_write_with_existing_content(self, changelog_md, ctx):
        changelog_md.write_text(
            """# Changelog

## 0.0.1

### header

- line1
- line2
- line3
""",
        )

        w = writer.MdWriter(changelog_md, ctx)
        w.add_version("0.0.2")
        w.add_section(
            "header",
            [
                Change("header", "line4", "fix", footers=[Footer("Refs", ": ", "#4")]),
                Change("header", "line5", "fix", footers=[Footer("Refs", ": ", "#5")]),
                Change("header", "line6", "fix", scope="config", footers=[Footer("Refs", ": ", "#6")]),
            ],
        )

        w.write()

        assert (
            changelog_md.read_text()
            == """# Changelog

## 0.0.2

### header

- (`config`) line6
- line4
- line5

## 0.0.1

### header

- line1
- line2
- line3
"""
        )


class TestRstWriter:
    def test_init(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)

        assert w.content == []
        assert w.dry_run is False

    def test_init_dry_run(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx, dry_run=True)

        assert w.content == []
        assert w.dry_run is True

    def test_init_no_existing_entries(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)

        assert w.existing == []

    def test_init_stores_existing_changelog(self, changelog_rst, ctx):
        changelog_rst.write_text(
            """=========
Changelog
=========

0.0.1
=====

header
------

* line1

* line2

* line3
""",
        )

        w = writer.RstWriter(changelog_rst, ctx)

        assert w.existing == [
            "0.0.1",
            "=====",
            "",
            "header",
            "------",
            "",
            "* line1",
            "",
            "* line2",
            "",
            "* line3",
            "",
        ]

    def test_add_version(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)

        w._add_version("0.0.0")

        assert w.content == ["0.0.0", "=====", ""]

    def test_add_section_header(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)

        w._add_section_header("header")

        assert w.content == ["header", "------", ""]

    def test_add_section_line(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)

        w._add_section_line(Change("header", "line", "fix", footers=[Footer("Refs", ": ", "#1")]))

        assert w.content == ["* line", ""]

    def test_add_section_line_with_metadata(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)

        w._add_section_line(
            Change("header", "line", "fix", scope="config", breaking=True, footers=[Footer("Authors", ": ", "(a, b)")]),
        )

        assert w.content == ["* (`config`) **Breaking** line (a, b)", ""]

    def test_add_section_line_with_links(self, changelog_rst):
        ctx = Context(Config(current_version="0.0.0", issue_link="http://url/issues/::issue_ref::"))
        w = writer.RstWriter(changelog_rst, ctx)

        w._add_section_line(
            Change(
                "header",
                "line",
                "fix",
                links=[Link("#1", "http://url/issues/1"), Link("1234567", "http://url/commit/commit-hash")],
            ),
        )

        assert w.content == ["* line [`#1`_] [`1234567`_]", ""]
        assert w._links == {"#1": "http://url/issues/1", "1234567": "http://url/commit/commit-hash"}
        assert w.links == [".. _`#1`: http://url/issues/1", ".. _`1234567`: http://url/commit/commit-hash"]

    def test_add_section_line_without_links(self, changelog_rst):
        ctx = Context(Config(current_version="0.0.0", commit_link="http://url/commit/::commit_hash::"))
        w = writer.RstWriter(changelog_rst, ctx)

        w._add_section_line(Change("header", "line", "fix"))

        assert w.content == ["* line", ""]
        assert w._links == {}
        assert w.links == []

    def test_str_with_links(self, changelog_rst):
        ctx = Context(Config(current_version="0.0.0", issue_link="http://url/issues/::issue_ref::"))
        w = writer.RstWriter(changelog_rst, ctx)

        w.add_version("0.0.1")
        w.add_section(
            "header",
            [
                Change("header", "line1", "fix", links=[Link("#1", "http://url/issues/1")]),
                Change("header", "line2", "fix", links=[Link("#2", "http://url/issues/2")]),
                Change("header", "line3", "fix", scope="config", links=[Link("#3", "http://url/issues/3")]),
            ],
        )

        assert (
            str(w)
            == """

0.0.1
=====

header
------

* (`config`) line3 [`#3`_]

* line1 [`#1`_]

* line2 [`#2`_]

.. _`#1`: http://url/issues/1
.. _`#2`: http://url/issues/2
.. _`#3`: http://url/issues/3

"""
        )

    def test_write_dry_run_doesnt_write_to_file(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx, dry_run=True)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            [
                Change("header", "line1", "fix", footers=[Footer("Refs", ": ", "#1")]),
                Change("header", "line2", "fix", footers=[Footer("Refs", ": ", "#2")]),
                Change("header", "line3", "fix", scope="config", footers=[Footer("Refs", ": ", "#3")]),
            ],
        )

        w.write()
        assert (
            changelog_rst.read_text()
            == """=========
Changelog
=========
"""
        )

    def test_write(self, changelog_rst, ctx):
        w = writer.RstWriter(changelog_rst, ctx)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            [
                Change("header", "line1", "fix", footers=[Footer("Refs", ": ", "#1")]),
                Change("header", "line2", "fix", footers=[Footer("Refs", ": ", "#2")]),
                Change("header", "line3", "fix", scope="config", footers=[Footer("Refs", ": ", "#3")]),
            ],
        )

        w.write()
        assert (
            changelog_rst.read_text()
            == """=========
Changelog
=========

0.0.1
=====

header
------

* (`config`) line3

* line1

* line2
"""
        )

    def test_write_with_existing_content(self, changelog_rst):
        changelog_rst.write_text(
            """=========
Changelog
=========

0.0.1
=====

header
------

* line1

* line2

* line3
""",
        )

        ctx = Context(Config(current_version="0.0.0", issue_link="http://url/issues/::issue_ref::"))
        w = writer.RstWriter(changelog_rst, ctx)
        w.add_version("0.0.2")
        w.add_section(
            "header",
            [
                Change("header", "line4", "fix", footers=[Footer("Refs", ": ", "#4")]),
                Change("header", "line5", "fix", footers=[Footer("Refs", ": ", "#5")]),
                Change("header", "line6", "fix", scope="config", footers=[Footer("Refs", ": ", "#6")]),
            ],
        )

        w.write()

        assert (
            changelog_rst.read_text()
            == """=========
Changelog
=========

0.0.2
=====

header
------

* (`config`) line6

* line4

* line5

0.0.1
=====

header
------

* line1

* line2

* line3
"""
        )


class TestNewWriter:
    @pytest.mark.parametrize(
        ("extension", "expected"),
        [
            (writer.Extension.MD, writer.MdWriter),
            (writer.Extension.RST, writer.RstWriter),
        ],
    )
    @pytest.mark.parametrize("dry_run", [True, False])
    def test_supported_format(self, extension, expected, dry_run):
        ctx = mock.Mock()
        w = writer.new_writer(ctx, extension, dry_run=dry_run)

        assert isinstance(w, expected)
        assert w.extension == extension
        assert w.changelog == pathlib.Path(f"CHANGELOG.{extension.value}")
        assert w.dry_run == dry_run

    def test_dry_run_default(self):
        ctx = mock.Mock()
        w = writer.new_writer(ctx, writer.Extension.MD)

        assert w.dry_run is False

    def test_unsupported_format(self):
        ctx = mock.Mock()
        ext = mock.Mock(value="txt")

        with pytest.raises(ValueError, match='Changelog extension "txt" not supported.') as e:
            writer.new_writer(ctx, ext)

        assert str(e.value) == 'Changelog extension "txt" not supported.'
