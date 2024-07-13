# Post processing

After a release is generated, all commits that contain an issue reference can
be processed to update an external source with details of the version release.
This allows issues in jira, notion etc to be updated with the version it was
released as a part of.

The configured post process url should contain an `::issue_ref::` place holder,
when processing each commit issue, the url will be dynamically updated before
being called.

By default the url will be called using a `POST` request, but the http verb can
be changed depending on the service being called, and its requirements. The
request
[body](https://nrwldev.github.io/changelog-gen/configuration/#post_process) can
also be configured with a `::version::` placeholder to add a comment to an
existing issue.

Optional headers can also be configured.

## Authorization

Currently only basic auth is supported, but if you find yourself with a usecase
that needs a different form of authentication, please raise an issue. To
provide authorization, configure an environment key to pull the authorization
values from using `post_process.auth_env`.

For basic auth, the environment variable should be in the format
`{user}:{api_key}`.
