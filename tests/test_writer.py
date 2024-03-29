from unittest import mock

import pytest

from changelog_gen import writer
from changelog_gen.config import Config
from changelog_gen.extractor import Change


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
def cfg():
    return Config()


@pytest.mark.parametrize(
    ("extension", "expected_cls"),
    [
        (writer.Extension.MD, writer.MdWriter),
        (writer.Extension.RST, writer.RstWriter),
    ],
)
def test_new_writer(extension, expected_cls, cfg):
    assert isinstance(writer.new_writer(extension, cfg), expected_cls)


def test_new_writer_raises_for_unsupported_extension(cfg):
    with pytest.raises(ValueError, match='Changelog extension "txt" not supported.'):
        writer.new_writer(mock.Mock(value="txt"), cfg)


class TestBaseWriter:
    def test_init(self, changelog, cfg):
        w = writer.BaseWriter(changelog, cfg)

        assert w.content == []
        assert w.dry_run is False

    def test_init_dry_run(self, changelog, cfg):
        w = writer.BaseWriter(changelog, cfg, dry_run=True)

        assert w.content == []
        assert w.dry_run is True

    def test_init_no_existing_entries(self, changelog, cfg):
        w = writer.BaseWriter(changelog, cfg)

        assert w.existing == []

    def test_init_stores_existing_changelog(self, changelog, cfg):
        changelog.write_text(
            """
## 0.0.1

### header

- line1
- line2
- line3
""",
        )
        w = writer.BaseWriter(changelog, cfg)

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

    def test_content_as_str(self, changelog, cfg):
        w = writer.BaseWriter(changelog, cfg)
        w.content = ["line1", "line2", "line3"]

        assert str(w) == "\n\nline1\nline2\nline3\n\n"

    def test_base_methods_not_implemented(self, changelog, cfg):
        w = writer.BaseWriter(changelog, cfg)

        with pytest.raises(NotImplementedError):
            w._add_section_header("header")

        with pytest.raises(NotImplementedError):
            w._add_section_line("description", Change("issue_ref", "description", "fix"))

        with pytest.raises(NotImplementedError):
            w._add_version("0.0.0")

    def test_add_version(self, monkeypatch, changelog, cfg):
        monkeypatch.setattr(writer.BaseWriter, "_add_version", mock.Mock())
        w = writer.BaseWriter(changelog, cfg)

        w.add_version("0.0.0")

        assert w._add_version.call_args == mock.call("0.0.0")

    def test_add_section(self, monkeypatch, changelog, cfg):
        monkeypatch.setattr(writer.BaseWriter, "_add_section_header", mock.Mock())
        monkeypatch.setattr(writer.BaseWriter, "_add_section_line", mock.Mock())

        w = writer.BaseWriter(changelog, cfg)

        w.add_section(
            "header",
            {
                "1": Change("1", "line1", "fix", breaking=True),
                "2": Change("2", "line2", "fix", authors="(a, b)"),
                "3": Change("3", "line3", "fix", scope="(config)"),
            },
        )

        assert w._add_section_header.call_args == mock.call("header")
        assert w._add_section_line.call_args_list == [
            mock.call("**Breaking:** line1", Change("1", "line1", "fix", breaking=True)),
            mock.call("(config) line3", Change("3", "line3", "fix", scope="(config)")),
            mock.call("line2 (a, b)", Change("2", "line2", "fix", authors="(a, b)")),
        ]

    def test_add_section_sorting(self, monkeypatch, changelog, cfg):
        monkeypatch.setattr(writer.BaseWriter, "_add_section_header", mock.Mock())
        monkeypatch.setattr(writer.BaseWriter, "_add_section_line", mock.Mock())

        w = writer.BaseWriter(changelog, cfg)

        w.add_section(
            "header",
            {
                "3": Change("3", "line3", "fix", breaking=True),
                "2": Change("2", "line2", "fix", authors="(a, b)"),
                "1": Change("1", "line1", "fix", scope="(config)"),
            },
        )

        assert w._add_section_header.call_args == mock.call("header")
        assert w._add_section_line.call_args_list == [
            mock.call("**Breaking:** line3", Change("3", "line3", "fix", breaking=True)),
            mock.call("(config) line1", Change("1", "line1", "fix", scope="(config)")),
            mock.call("line2 (a, b)", Change("2", "line2", "fix", authors="(a, b)")),
        ]


class TestMdWriter:
    def test_init(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)

        assert w.content == []
        assert w.dry_run is False

    def test_init_dry_run(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg, dry_run=True)

        assert w.content == []
        assert w.dry_run is True

    def test_init_no_existing_entries(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)

        assert w.existing == []

    def test_init_stores_existing_changelog(self, changelog_md, cfg):
        changelog_md.write_text(
            """# Changelog

## 0.0.1

### header

- line1
- line2
- line3
""",
        )

        w = writer.MdWriter(changelog_md, cfg)

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

    def test_add_version(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)

        w._add_version("0.0.0")

        assert w.content == ["## 0.0.0", ""]

    def test_add_section_header(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_header("header")

        assert w.content == ["### header", ""]

    def test_add_section_line(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_line("line", Change("1", "line", "fix"))

        assert w.content == ["- line [#1]"]

    def test_add_section_line_ignores_placeholder(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix"))

        assert w.content == ["- line"]

    def test_add_section_line_with_issue_link(self, changelog_md):
        cfg = Config(issue_link="http://url/issues/::issue_ref::")
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_line("line", Change("1", "line", "fix"))

        assert w.content == ["- line [[#1](http://url/issues/1)]"]

    def test_add_section_line_with_issue_link_ignores_placeholder(self, changelog_md):
        cfg = Config(issue_link="http://url/issues/::issue_ref::")
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix"))

        assert w.content == ["- line"]

    def test_add_section_line_with_commit_link(self, changelog_md):
        cfg = Config(commit_link="http://url/commit/::commit_hash::")
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix", short_hash="1234567", commit_hash="commit-hash"))

        assert w.content == ["- line [[1234567](http://url/commit/commit-hash)]"]

    def test_add_section_line_with_commit_link_ignores_null_commit_hash(self, changelog_md):
        cfg = Config(commit_link="http://url/commit/::commit_hash::")
        w = writer.MdWriter(changelog_md, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix"))

        assert w.content == ["- line"]

    def test_write_dry_run_doesnt_write_to_file(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg, dry_run=True)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            {
                "1": Change("1", "line1", "fix"),
                "2": Change("2", "line2", "fix"),
                "3": Change("3", "line3", "fix", scope="(config)"),
            },
        )

        w.write()
        assert changelog_md.read_text() == """# Changelog\n"""

    def test_write(self, changelog_md, cfg):
        w = writer.MdWriter(changelog_md, cfg)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            {
                "1": Change("1", "line1", "fix"),
                "2": Change("2", "line2", "fix"),
                "3": Change("3", "line3", "fix", scope="(config)"),
            },
        )

        w.write()
        assert (
            changelog_md.read_text()
            == """# Changelog

## 0.0.1

### header

- (config) line3 [#3]
- line1 [#1]
- line2 [#2]
"""
        )

    def test_write_with_existing_content(self, changelog_md, cfg):
        changelog_md.write_text(
            """# Changelog

## 0.0.1

### header

- line1
- line2
- line3
""",
        )

        w = writer.MdWriter(changelog_md, cfg)
        w.add_version("0.0.2")
        w.add_section(
            "header",
            {
                "4": Change("4", "line4", "fix"),
                "5": Change("5", "line5", "fix"),
                "6": Change("6", "line6", "fix", scope="(config)"),
            },
        )

        w.write()

        assert (
            changelog_md.read_text()
            == """# Changelog

## 0.0.2

### header

- (config) line6 [#6]
- line4 [#4]
- line5 [#5]

## 0.0.1

### header

- line1
- line2
- line3
"""
        )


class TestRstWriter:
    def test_init(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)

        assert w.content == []
        assert w.dry_run is False

    def test_init_dry_run(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg, dry_run=True)

        assert w.content == []
        assert w.dry_run is True

    def test_init_no_existing_entries(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)

        assert w.existing == []

    def test_init_stores_existing_changelog(self, changelog_rst, cfg):
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

        w = writer.RstWriter(changelog_rst, cfg)

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

    def test_add_version(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_version("0.0.0")

        assert w.content == ["0.0.0", "=====", ""]

    def test_add_section_header(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_header("header")

        assert w.content == ["header", "------", ""]

    def test_add_section_line(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_line("line", Change("1", "line", "fix"))

        assert w.content == ["* line [#1]", ""]

    def test_add_section_line_ignores_placeholder(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix"))

        assert w.content == ["* line", ""]

    def test_add_section_line_with_issue_link(self, changelog_rst):
        cfg = Config(issue_link="http://url/issues/::issue_ref::")
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_line("line", Change("1", "line", "fix"))

        assert w.content == ["* line [`#1`_]", ""]
        assert w._links == {"#1": "http://url/issues/1"}
        assert w.links == [".. _`#1`: http://url/issues/1"]

    def test_add_section_line_with_issue_link_skips_placeholder(self, changelog_rst):
        cfg = Config(issue_link="http://url/issues/::issue_ref::")
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix"))

        assert w.content == ["* line", ""]
        assert w._links == {}
        assert w.links == []

    def test_add_section_line_with_commit_link(self, changelog_rst):
        cfg = Config(commit_link="http://url/commit/::commit_hash::")
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix", short_hash="1234567", commit_hash="commit-hash"))

        assert w.content == ["* line [`1234567`_]", ""]
        assert w._links == {"1234567": "http://url/commit/commit-hash"}
        assert w.links == [".. _`1234567`: http://url/commit/commit-hash"]

    def test_add_section_line_with_commit_link_ignores_null_commit_hash(self, changelog_rst):
        cfg = Config(commit_link="http://url/commit/::commit_hash::")
        w = writer.RstWriter(changelog_rst, cfg)

        w._add_section_line("line", Change("__1__", "line", "fix"))

        assert w.content == ["* line", ""]
        assert w._links == {}
        assert w.links == []

    def test_str_with_links(self, changelog_rst):
        cfg = Config(issue_link="http://url/issues/::issue_ref::")
        w = writer.RstWriter(changelog_rst, cfg)

        w.add_version("0.0.1")
        w.add_section(
            "header",
            {
                "1": Change("1", "line1", "fix"),
                "2": Change("2", "line2", "fix"),
                "3": Change("3", "line3", "fix", scope="(config)"),
            },
        )

        assert (
            str(w)
            == """

0.0.1
=====

header
------

* (config) line3 [`#3`_]

* line1 [`#1`_]

* line2 [`#2`_]

.. _`#1`: http://url/issues/1
.. _`#2`: http://url/issues/2
.. _`#3`: http://url/issues/3

"""
        )

    def test_write_dry_run_doesnt_write_to_file(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg, dry_run=True)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            {
                "1": Change("1", "line1", "fix"),
                "2": Change("2", "line2", "fix"),
                "3": Change("3", "line3", "fix", scope="(config)"),
            },
        )

        w.write()
        assert (
            changelog_rst.read_text()
            == """=========
Changelog
=========
"""
        )

    def test_write(self, changelog_rst, cfg):
        w = writer.RstWriter(changelog_rst, cfg)
        w.add_version("0.0.1")
        w.add_section(
            "header",
            {
                "1": Change("1", "line1", "fix"),
                "2": Change("2", "line2", "fix"),
                "3": Change("3", "line3", "fix", scope="(config)"),
            },
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

* (config) line3 [#3]

* line1 [#1]

* line2 [#2]
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

        cfg = Config(issue_link="http://url/issues/::issue_ref::")
        w = writer.RstWriter(changelog_rst, cfg)
        w.add_version("0.0.2")
        w.add_section(
            "header",
            {
                "4": Change("4", "line4", "fix"),
                "5": Change("5", "line5", "fix"),
                "6": Change("6", "line6", "fix", scope="(config)"),
            },
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

* (config) line6 [`#6`_]

* line4 [`#4`_]

* line5 [`#5`_]

0.0.1
=====

header
------

* line1

* line2

* line3

.. _`#4`: http://url/issues/4
.. _`#5`: http://url/issues/5
.. _`#6`: http://url/issues/6"""
        )
