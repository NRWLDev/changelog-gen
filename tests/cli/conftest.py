import pytest
import typer.testing

import changelog_gen.cli.command


class CliRunner(typer.testing.CliRunner):
    target = changelog_gen.cli.command.app

    def invoke(self, *args, **kwargs):
        result = super().invoke(self.target, *args, **kwargs)
        if result.exception:
            if isinstance(result.exception, SystemExit):
                # The error is already properly handled. Print it and return.
                print(result.output)  # noqa: T201
            else:
                raise result.exception.with_traceback(result.exc_info[2])
        return result


@pytest.fixture
def cli_runner():
    return CliRunner()
