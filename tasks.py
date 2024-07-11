"""Collection of useful commands for `changelog-gen` management.

To view a list of available commands:

$ invoke --list
"""

import invoke


@invoke.task
def install(context):
    """Install production requirements for `backend`."""
    context.run("poetry install --only main")


@invoke.task
def install_dev(context):
    """Install development requirements for `backend`."""
    context.run("poetry install --extras legacy postprocess")
    context.run("poetry run pre-commit install")
