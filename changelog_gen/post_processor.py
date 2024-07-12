from __future__ import annotations

import os
import typing as t
from http import HTTPStatus

import httpx
import typer

from changelog_gen.util import timer

if t.TYPE_CHECKING:
    from changelog_gen.config import PostProcessConfig
    from changelog_gen.context import Context


class BearerAuth(httpx.Auth):
    """Implement Bearer token auth class for httpx."""

    def __init__(self: t.Self, token: str) -> None:
        self.token = f"Bearer {token}"

    def auth_flow(self: t.Self, request: httpx.Request) -> t.Generator[httpx.Request, httpx.Response, None]:
        """Send the request, with bearer token."""
        request.headers["Authorization"] = self.token
        yield request


def make_client(context: Context, cfg: PostProcessConfig) -> httpx.Client:
    """Generate HTTPx client with authorization if configured."""
    auth = None
    if cfg.auth_env:
        user_auth = os.environ.get(cfg.auth_env)
        if not user_auth:
            context.error('Missing environment variable "%s"', cfg.auth_env)
            raise typer.Exit(code=1)

        if cfg.auth_type == "bearer":
            auth = BearerAuth(user_auth)
        else:
            # Fall back to basic auth
            try:
                username, api_key = user_auth.split(":")
            except ValueError as e:
                context.error(
                    "Unexpected content in %s, need '{{username}}:{{api_key}}' for basic auth",
                    cfg.auth_env,
                )
                raise typer.Exit(code=1) from e
            else:
                auth = httpx.BasicAuth(username=username, password=api_key)

    return httpx.Client(
        auth=auth,
        headers=cfg.headers,
    )


@timer
def per_issue_post_process(
    context: Context,
    cfg: PostProcessConfig,
    issue_refs: list[str],
    version_tag: str,
    *,
    dry_run: bool = False,
) -> None:
    """Run post process for all provided issue references."""
    if not cfg.url:
        return
    context.warning("Post processing:")

    client = make_client(context, cfg)

    for issue in issue_refs:
        url, body = cfg.url, cfg.body
        for find, replace in [
            ("::issue_ref::", issue),
            ("::version::", version_tag),
        ]:
            url = url.replace(find, replace)
            body = body.replace(find, replace)

        context.indent()
        if dry_run:
            context.warning("Would request: %s %s %s", cfg.verb, url, body)
        else:
            context.info("Request: %s %s", cfg.verb, url)
            r = client.request(
                method=cfg.verb,
                url=url,
                content=body,
            )
            context.indent()
            try:
                context.info("Response: %s", HTTPStatus(r.status_code).name)
                r.raise_for_status()
            except httpx.HTTPError as e:
                context.error("Post process request failed.")
                context.warning("%s", e.response.text)
    context.reset()
