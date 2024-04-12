import pytest

from changelog_gen import writer
from changelog_gen.cli import util


@pytest.mark.parametrize(
    ("filename", "ext"),
    [
        ("CHANGELOG.md", writer.Extension.MD),
        ("CHANGELOG.rst", writer.Extension.RST),
        ("CHANGELOG.txt", None),
    ],
)
def test_detect_extension(filename, ext, cwd):
    f = cwd / filename
    f.write_text("changelog")

    assert util.detect_extension() == ext


@pytest.mark.parametrize(
    ("envkey", "envval", "expected"),
    [
        ("VISUAL", "emacs", "emacs"),
        ("EDITOR", "vim", "vim"),
        (None, None, "vi"),
    ],
)
def test_get_editor(envkey, envval, expected, monkeypatch):
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    if envkey:
        monkeypatch.setenv(envkey, envval)

    assert util.get_editor() == expected
