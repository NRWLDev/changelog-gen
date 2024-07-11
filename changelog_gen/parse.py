from __future__ import annotations

import contextlib
import re

from changelog_gen import errors


def parse(regex: str, version: str) -> dict[str, str | None]:
    """Parse a version into parts dict."""
    m = re.match(regex, version)
    if m is None:
        msg = "Can't parse version string."
        raise errors.ParseError(msg)

    return m.groupdict()


def serialise(patterns: list[str], version_parts: dict[str, str | None]) -> str:
    """Serialise version parts into a version string."""
    serialise_parts = {k: v for k, v in version_parts.items() if v is not None}
    for pattern in patterns:
        with contextlib.suppress(KeyError):
            return pattern.format(**serialise_parts)

    msg = "Can't serialise version."
    raise errors.SerialiseError(msg)


def bump(
    version_parts: dict[str, str | None],
    component: str,
    component_config: dict[str, list[str]],
) -> dict[str, str | None]:
    """Increment version component."""
    # Validate component in parts
    components = list(version_parts.keys())
    dependents = components[components.index(component) + 1 :]
    for dependent in dependents:
        reset = component_config.get(dependent, ["0"])[0]
        version_parts[dependent] = reset

    if component in component_config:
        current = version_parts[component]
        options = component_config[component]
        if current is None:
            msg = "Can't increment unset optional component."
            raise errors.BumpError(msg)

        if current == options[-1]:
            new = None
            dependents = components[components.index(component) + 1 :]
            for dependent in dependents:
                version_parts[dependent] = None
        else:
            new = options[options.index(current) + 1]
    else:
        new = str(int(version_parts[component]) + 1)

    version_parts[component] = new

    return version_parts
