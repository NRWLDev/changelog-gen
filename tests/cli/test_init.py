import pytest


@pytest.mark.parametrize(
    ("filename", "ext"),
    [
        ("CHANGELOG.md", "md"),
        ("CHANGELOG.rst", "rst"),
    ],
)
def test_init_aborts_if_file_exists(cwd, cli_runner, filename, ext):
    f = cwd / filename
    f.write_text("changelog")

    result = cli_runner.invoke(["init", "--file-format", ext])

    assert result.exit_code == 1
    assert result.output.strip() == f"{filename} detected."


@pytest.mark.parametrize(
    ("filename", "ext"),
    [
        ("CHANGELOG.md", "md"),
        ("CHANGELOG.rst", "rst"),
    ],
)
def test_init_writes_file(cwd, cli_runner, filename, ext):
    result = cli_runner.invoke(["init", "--file-format", ext])

    assert result.exit_code == 0

    f = cwd / filename
    assert f.exists()
