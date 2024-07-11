import contextlib
import re


def parse(regex: str, version: str) -> dict[str, str]:
    """Parse a version into parts dict."""
    m = re.match(regex, version)
    if m is None:
        raise Exception("Can't parse version string.")  # noqa: TRY002, TRY003, EM101

    return {k: v for k, v in m.groupdict().items() if v is not None}


def serialise(patterns: list[str], version_parts: dict[str, str]) -> str:
    """Serialise version parts into a version string."""
    for pattern in patterns:
        with contextlib.suppress(KeyError):
            return pattern.format(**version_parts)

    raise Exception("Can't serialize version.")  # noqa: TRY002, TRY003, EM101
