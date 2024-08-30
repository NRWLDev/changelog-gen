# Post processing

After a release is generated, all commits that contain an issue reference can
be processed to update an external source with details of the version release.
This allows issues in jira, notion etc to be updated with the version it was
released as a part of.

The configured [post
process](https://nrwldev.github.io/changelog-gen/configuration/#post_process)
link generator can refer to any extracted information, if an extractor matches
multiple times, the post process will be called for each match for that change.

By default the generated link will be called using a `POST` request, but the
http verb can be changed depending on the service being called, and its
requirements. The request
[body](https://nrwldev.github.io/changelog-gen/configuration/#post_processbody_template)
can also be configured with a jinja template, provided at render time will be
the `version` string, the `source` from the extracted match, and all
information extracted via `extractors`.

Optional
[headers](https://nrwldev.github.io/changelog-gen/configuration/#post_processheaders)
can also be configured.

## Authorization

Currently basic auth, bearer tokens, and signed aws4 are supported, but if you find
yourself with a usecase that needs a different form of authentication, please
raise an issue. To provide authorization, configure an environment key to pull
the authorization values from using
[auth_env](https://nrwldev.github.io/changelog-gen/configuration/#post_processauth_env)

For basic auth, the environment variable should be in the format
`{user}:{api_key}`.

For bearer auth, the environment variable should be in the format `{api_key}`.

For AWS4 signed auth, the environment variable should be in the format `{access_key_id}:{secret_access_key}:{service_name}:{region}`.

## Installation

To use post_process functionality, there are some optional dependencies that
need to be installed. Due to the implementation using httpx, post_process is
not supported on python3.8.

```sh
pip install changelog-gen[post-process]
```
