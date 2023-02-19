from http import HTTPStatus
from unittest import mock

import click
import pytest
import requests
from requests.auth import HTTPBasicAuth
from requests_mock import mock as request_mock

from changelog_gen import post_processor
from changelog_gen.config import PostProcessConfig


class TestMakeSession:
    def test_create_session_with_auth_token(self, monkeypatch):
        monkeypatch.setenv("MY_API_AUTH", "fake_auth@domain:hex_api_key")
        cfg = PostProcessConfig(auth_env="MY_API_AUTH")

        conn = post_processor.make_session(cfg)

        assert conn.headers == {"content-type": "application/json"}
        assert isinstance(conn.auth, HTTPBasicAuth)
        assert conn.auth.username == "fake_auth@domain"
        assert conn.auth.password == "hex_api_key"  # nosec: B105

    def test_create_session_without_auth_token(self):
        cfg = PostProcessConfig()

        conn = post_processor.make_session(cfg)

        assert conn.headers == {"content-type": "application/json"}
        assert conn.auth is None

    def test_handle_no_auth_data_gracefully(self, monkeypatch):
        monkeypatch.setattr(
            post_processor.click,
            "echo",
            mock.Mock(),
        )

        cfg = PostProcessConfig(auth_env="MY_API_AUTH")

        with pytest.raises(click.Abort):
            post_processor.make_session(cfg)

        assert post_processor.click.echo.call_args == mock.call(
            'Missing environment variable "MY_API_AUTH"',
        )

    @pytest.mark.parametrize(
        "env_value",
        [
            "fake_auth@domain:hex_api_key:toomuch",
            "fake_auth@domain",
        ],
    )
    def test_handle_bad_auth_gracefully(self, monkeypatch, env_value):
        monkeypatch.setattr(
            post_processor.click,
            "echo",
            mock.Mock(),
        )
        monkeypatch.setenv("MY_API_AUTH", env_value)

        cfg = PostProcessConfig(auth_env="MY_API_AUTH")

        with pytest.raises(click.Abort):
            post_processor.make_session(cfg)

        assert post_processor.click.echo.call_args == mock.call(
            'Unexpected content in MY_API_AUTH, need "{username}:{api_key}"',
        )


class TestPerIssuePostPrequest:
    @pytest.mark.parametrize("cfg_verb", ["POST", "PUT", "GET"])
    @pytest.mark.parametrize(
        "issue_refs",
        [
            ["1", "2", "3"],
            [],
        ],
    )
    def test_one_request_per_issue(self, monkeypatch, requests_mock, cfg_verb, issue_refs):
        monkeypatch.setattr(
            post_processor,
            "make_session",
            mock.Mock(return_value=requests.Session()),
        )
        cfg = PostProcessConfig(
            verb=cfg_verb,
            url="https://my-api.github.com/comments/{issue_ref}",
        )
        for issue in issue_refs:
            requests_mock.request(
                cfg_verb,
                cfg.url.format(issue_ref=issue),
                status_code=HTTPStatus.OK,
            )

        post_processor.per_issue_post_process(cfg, issue_refs, "1.0.0")

        assert post_processor.make_session.call_count == 1

    def test_handle_http_errors_gracefully(self, requests_mock, monkeypatch):
        issue_refs = ["1", "2", "3"]

        cfg = PostProcessConfig(url="https://my-api.github.com/comments/{issue_ref}")

        ep0 = cfg.url.format(issue_ref=issue_refs[0])
        requests_mock.request(
            "POST",
            ep0,
            status_code=HTTPStatus.OK,
        )
        ep1 = cfg.url.format(issue_ref=issue_refs[1])
        not_found_txt = f"{issue_refs[1]} NOT FOUND"
        requests_mock.request(
            "POST",
            ep1,
            status_code=HTTPStatus.NOT_FOUND,
            text=not_found_txt,
        )
        ep2 = cfg.url.format(issue_ref=issue_refs[2])
        requests_mock.request(
            "POST",
            ep2,
            status_code=HTTPStatus.OK,
        )

        monkeypatch.setattr(post_processor.click, "echo", mock.Mock())

        post_processor.per_issue_post_process(cfg, issue_refs, "1.0.0")

        # 1 line for each successful post and 2 lines for the failure
        assert post_processor.click.echo.call_count == 4  # noqa: PLR2004
        assert post_processor.click.echo.call_args_list == [
            mock.call(f"POST {ep0}: OK"),
            mock.call(f"POST {ep1}: NOT_FOUND"),
            mock.call(not_found_txt),
            mock.call(f"POST {ep2}: OK"),
        ]

    @pytest.mark.parametrize("cfg_verb", ["POST", "PUT", "GET"])
    @pytest.mark.parametrize("new_version", ["1.0.0", "3.2.1"])
    @pytest.mark.parametrize(
        ("cfg_body", "exp_body"),
        [
            (None, '{"body": "Released on v%s"}'),
            # send issue ref as an int without quotes
            ('{{"issue": {issue_ref}, "version": "{new_version}"}}', '{"issue": 1, "version": "%s"}'),
        ],
    )
    def test_body(self, cfg_verb, new_version, cfg_body, exp_body):
        kwargs = {
            "verb": cfg_verb,
        }
        if cfg_body is not None:
            kwargs["body"] = cfg_body
        cfg = PostProcessConfig(
            url="https://my-api.github.com/comments/{issue_ref}",
            **kwargs,
        )
        with request_mock() as m:
            m.request(
                cfg_verb,
                cfg.url.format(issue_ref=1),
                status_code=HTTPStatus.OK,
            )

            post_processor.per_issue_post_process(cfg, ["1"], new_version)

            assert m.call_count == 1
            assert m.request_history[0].text == exp_body % new_version

    @pytest.mark.parametrize("cfg_verb", ["POST", "PUT", "GET"])
    @pytest.mark.parametrize(
        "issue_refs",
        [
            ["1", "2", "3"],
            [],
        ],
    )
    @pytest.mark.parametrize(
        ("cfg_body", "exp_body"),
        [
            (None, '{{"body": "Released on v3.2.1"}}'),
            # send issue ref as an int without quotes
            ('{{"issue": {issue_ref}, "version": "{new_version}"}}', '{{"issue": {issue_ref}, "version": "3.2.1"}}'),
        ],
    )
    def test_dry_run(self, monkeypatch, cfg_verb, issue_refs, cfg_body, exp_body):  # noqa: PLR0913
        kwargs = {}
        if cfg_body is not None:
            kwargs["body"] = cfg_body
        cfg = PostProcessConfig(
            url="https://my-api.github.com/comments/{issue_ref}",
            verb=cfg_verb,
            **kwargs,
        )
        monkeypatch.setattr(
            post_processor.click,
            "echo",
            mock.Mock(),
        )

        post_processor.per_issue_post_process(
            cfg,
            issue_refs,
            "3.2.1",
            dry_run=True,
        )

        assert post_processor.click.echo.call_args_list == [
            mock.call(f"{cfg_verb} {cfg.url.format(issue_ref=issue)} {exp_body.format(issue_ref=issue)}")
            for issue in issue_refs
        ]
