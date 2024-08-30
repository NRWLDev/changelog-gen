from http import HTTPStatus
from unittest import mock

import pytest
import typer
from aws4.key_pair import KeyPair

from changelog_gen import post_processor
from changelog_gen.config import PostProcessConfig
from changelog_gen.extractor import Change

httpx = pytest.importorskip("httpx")


def test_bearer_auth_flow():
    req = mock.Mock(
        headers={},
    )
    a = post_processor.BearerAuth("token")

    assert a.token == "Bearer token"
    r = next(a.auth_flow(req))
    assert r.headers["Authorization"] == "Bearer token"


class TestMakeClient:
    def test_create_client_with_basic_auth_token(self, monkeypatch):
        monkeypatch.setenv("MY_API_AUTH", "fake_auth@domain:hex_api_key")
        cfg = PostProcessConfig(auth_env="MY_API_AUTH", headers={"content-type": "application/json"})

        client = post_processor.make_client(mock.Mock(), cfg)

        assert client.headers["content-type"] == "application/json"
        assert client.auth._auth_header == "Basic ZmFrZV9hdXRoQGRvbWFpbjpoZXhfYXBpX2tleQ=="

    def test_create_client_with_bearer_auth_token(self, monkeypatch):
        monkeypatch.setenv("AUTH_TOKEN", "hex_api_key")
        cfg = PostProcessConfig(auth_env="AUTH_TOKEN", headers={"content-type": "application/json"}, auth_type="bearer")

        client = post_processor.make_client(mock.Mock(), cfg)

        assert client.headers["content-type"] == "application/json"
        assert client.auth.token == "Bearer hex_api_key"

    def test_create_client_with_signed_auth_token(self, monkeypatch):
        monkeypatch.setenv("AUTH_TOKEN", "access_key:secret_key:service_name:region")
        cfg = PostProcessConfig(auth_env="AUTH_TOKEN", headers={"content-type": "application/json"}, auth_type="aws4")

        client = post_processor.make_client(mock.Mock(), cfg)

        assert client.headers["content-type"] == "application/json"
        assert client.auth.key_pair == KeyPair("access_key", "secret_key")
        assert client.auth.service == "service_name"
        assert client.auth.region == "region"

    def test_create_client_without_auth_token(self):
        cfg = PostProcessConfig(headers={"content-type": "application/json"})

        client = post_processor.make_client(mock.Mock(), cfg)

        assert client.headers["content-type"] == "application/json"
        assert client.auth is None

    def test_handle_no_auth_data_gracefully(self):
        cfg = PostProcessConfig(auth_env="MY_API_AUTH")

        ctx = mock.Mock()
        with pytest.raises(typer.Exit) as e:
            post_processor.make_client(ctx, cfg)

        assert ctx.error.call_args == mock.call(
            'Missing environment variable "%s"',
            "MY_API_AUTH",
        )
        assert e.value.exit_code == 1

    @pytest.mark.parametrize(
        "env_value",
        [
            "fake_auth@domain:hex_api_key:toomuch",
            "fake_auth@domain",
        ],
    )
    def test_handle_bad_auth_gracefully(self, monkeypatch, env_value):
        monkeypatch.setenv("MY_API_AUTH", env_value)

        cfg = PostProcessConfig(auth_env="MY_API_AUTH")

        ctx = mock.Mock()
        with pytest.raises(typer.Exit) as e:
            post_processor.make_client(ctx, cfg)

        assert ctx.error.call_args == mock.call(
            "Unexpected content in %s, need '{{username}}:{{api_key}}' for basic auth",
            "MY_API_AUTH",
        )
        assert e.value.exit_code == 1


class TestPerIssuePostPrequest:
    @pytest.mark.parametrize("cfg_verb", ["POST", "PUT", "GET"])
    @pytest.mark.parametrize(
        "changes",
        [
            [
                Change("header", "line1", "fix", extractions={"issue_ref": ["1"]}),
                Change("header", "line2", "fix", extractions={"issue_ref": ["2"]}),
                Change("header", "line3", "fix"),
            ],
            [],
        ],
    )
    def test_one_client_regardless_of_issue_count(self, monkeypatch, httpx_mock, cfg_verb, changes):
        monkeypatch.setattr(
            post_processor,
            "make_client",
            mock.Mock(return_value=httpx.Client()),
        )
        cfg = PostProcessConfig(
            verb=cfg_verb,
            link_generator={"source": "issue_ref", "link": "https://my-api.github.com/comments/{0}"},
        )
        for change in changes:
            if "issue_ref" in change.extractions:
                httpx_mock.add_response(
                    method=cfg_verb,
                    url=f"https://my-api.github.com/comments/{change.extractions['issue_ref'][0].replace('#', '')}",
                    status_code=HTTPStatus.OK,
                )

        ctx = mock.Mock()
        post_processor.per_issue_post_process(ctx, cfg, changes, "1.0.0")

        assert post_processor.make_client.call_args_list == [
            mock.call(ctx, cfg),
        ]

    def test_handle_http_errors_gracefully(self, httpx_mock):
        ctx = mock.Mock()
        changes = [
            Change("header", "line1", "fix", extractions={"issue_ref": ["1"]}),
            Change("header", "line2", "fix", extractions={"issue_ref": ["2"]}),
            Change("header", "line3", "fix"),
        ]

        cfg = PostProcessConfig(
            link_generator={"source": "issue_ref", "link": "https://my-api.github.com/comments/{0}"},
        )

        ep0 = "https://my-api.github.com/comments/1"
        httpx_mock.add_response(
            method="POST",
            url=ep0,
            status_code=HTTPStatus.OK,
        )
        ep1 = "https://my-api.github.com/comments/2"
        not_found_txt = "2 NOT FOUND"
        httpx_mock.add_response(
            method="POST",
            url=ep1,
            status_code=HTTPStatus.NOT_FOUND,
            content=bytes(not_found_txt, "utf-8"),
        )

        post_processor.per_issue_post_process(ctx, cfg, changes, "1.0.0")

        assert ctx.error.call_args_list == [
            mock.call("Post process request failed."),
        ]
        assert ctx.warning.call_args_list == [
            mock.call("Post processing:"),
            mock.call("%s", not_found_txt),
        ]
        assert ctx.info.call_args_list == [
            mock.call("Request: %s %s", "POST", ep0),
            mock.call("Response: %s", "OK"),
            mock.call("Request: %s %s", "POST", ep1),
            mock.call("Response: %s", "NOT_FOUND"),
        ]

    @pytest.mark.parametrize("cfg_verb", ["POST", "PUT", "GET"])
    @pytest.mark.parametrize("new_version", ["1.0.0", "3.2.1"])
    @pytest.mark.parametrize(
        ("cfg_body", "exp_body"),
        [
            (None, '{"body": "Released on %s"}'),
            # send issue ref as an int without quotes
            ('{"issue": {{ source }}, "version": "{{ version }}"}', '{"issue": 1, "version": "%s"}'),
        ],
    )
    def test_body(self, cfg_verb, new_version, cfg_body, exp_body, httpx_mock):
        kwargs = {
            "verb": cfg_verb,
        }
        if cfg_body is not None:
            kwargs["body_template"] = cfg_body
        cfg = PostProcessConfig(
            link_generator={"source": "issue_ref", "link": "https://my-api.github.com/comments/{0}"},
            **kwargs,
        )
        httpx_mock.add_response(
            method=cfg_verb,
            url="https://my-api.github.com/comments/1",
            status_code=HTTPStatus.OK,
            match_content=bytes(exp_body % new_version, "utf-8"),
        )

        changes = [
            Change("header", "line1", "fix", extractions={"issue_ref": ["1"]}),
        ]
        post_processor.per_issue_post_process(mock.Mock(), cfg, changes, new_version)

    @pytest.mark.parametrize("cfg_verb", ["POST", "PUT", "GET"])
    @pytest.mark.parametrize(
        ("cfg_body", "exp_body"),
        [
            (None, '{"body": "Released on 3.2.1"}'),
            # send issue ref as an int without quotes
            ('{"issue": {{ source }}, "version": "{{ version }}"}', '{"issue": ::issue_ref::, "version": "3.2.1"}'),
        ],
    )
    def test_dry_run(self, cfg_verb, cfg_body, exp_body):
        kwargs = {
            "verb": cfg_verb,
        }
        if cfg_body is not None:
            kwargs["body_template"] = cfg_body
        cfg = PostProcessConfig(
            link_generator={"source": "issue_ref", "link": "https://my-api.github.com/comments/{0}"},
            **kwargs,
        )
        url = "https://my-api.github.com/comments/{0}"
        changes = [
            Change("header", "line1", "fix", extractions={"issue_ref": ["1"]}),
            Change("header", "line2", "fix", extractions={"issue_ref": ["2"]}),
            Change("header", "line3", "fix", extractions={"author": ["edgy"]}),
        ]

        ctx = mock.Mock()
        post_processor.per_issue_post_process(
            ctx,
            cfg,
            changes,
            "3.2.1",
            dry_run=True,
        )

        assert ctx.warning.call_args_list == [
            mock.call(
                "Post processing:",
            ),
        ] + [
            mock.call(
                "Would request: %s %s %s",
                cfg_verb,
                url.format(issue),
                exp_body.replace("::issue_ref::", issue),
            )
            for issue in ["1", "2"]
        ]

    def test_no_url_ignored(self):
        cfg = PostProcessConfig()
        ctx = mock.Mock()
        changes = [
            Change("header", "line1", "fix", extractions={"issue_ref": ["1"]}),
            Change("header", "line2", "fix", extractions={"issue_ref": ["2"]}),
            Change("header", "line3", "fix"),
        ]
        post_processor.per_issue_post_process(
            ctx,
            cfg,
            changes,
            "3.2.1",
            dry_run=True,
        )

        assert ctx.warning.call_args_list == []
