import re


def parse(regex: str, version: str) -> dict[str, str]:
    """Parse a version string."""
    m = re.match(regex, version)
    if m is None:
        raise Exception("Can't parse version string.")  # noqa: TRY002, TRY003, EM101

    return {k: v for k, v in m.groupdict().items() if v is not None}
