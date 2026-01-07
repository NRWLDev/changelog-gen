# Changelog

## v0.14.0 - 2026-01-07

### Features and Improvements

- **Breaking** Drop python 3.9 support. [[475d247](https://github.com/NRWLDev/changelog-gen/commit/475d2477448a804f25fcf7a3b97ea404603c9ee5)]

## v0.13.8 - 2025-05-05

### Documentation

- Add documentation url for pypi. [[478cc93](https://github.com/NRWLDev/changelog-gen/commit/478cc9349ad6b06f7f017520118852997003b059)]

## v0.13.7 - 2025-05-05

### Bug fixes

- Ensure urls render in pypi. [[c535c67](https://github.com/NRWLDev/changelog-gen/commit/c535c6729d81b03b8a2b05205b76a2978dae935e)]

## v0.13.6 - 2025-04-07

### Bug fixes

- Handle % chars in commit message descriptions. [[58](https://github.com/NRWLDev/changelog-gen/issues/58)] [[4baaf7e](https://github.com/NRWLDev/changelog-gen/commit/4baaf7e1e066cc3904ebf4c419488eaade3d0dd6)]

## v0.13.5 - 2024-11-23

### Bug fixes

- Support adding unknown files to git for hooks. [[12d2a08](https://github.com/NRWLDev/changelog-gen/commit/12d2a08133fe442dcd9295f0b0921075286da9df)]

## v0.13.4 - 2024-11-01

### Features and Improvements

- Support custom change and release templates with cli command to test template outputs. [[56](https://github.com/NRWLDev/changelog-gen/issues/56)] [[28eca08](https://github.com/NRWLDev/changelog-gen/commit/28eca083a3731bbc8559f935a3d866752ddb216f)]

## v0.13.3 - 2024-11-01

### Features and Improvements

- Support displaying specific config key from cli. [[454cb07](https://github.com/NRWLDev/changelog-gen/commit/454cb07cccb2d2fcbefef812ac1b9f8d16dc2f3e)]

## v0.13.2 - 2024-09-27

### Features and Improvements

- Add regex_replace jinja template filter. [[3418a8d](https://github.com/NRWLDev/changelog-gen/commit/3418a8de3b16441180567dae4d52108ce63b6662)]

## v0.13.1 - 2024-09-10

### Miscellaneous

- Relax dependency pins [[38057b4](https://github.com/NRWLDev/changelog-gen/commit/38057b466f97ee31539203385c297bb2900ab7ab)]

## v0.13.0 - 2024-09-09

### Miscellaneous

- **Breaking** Migrate from poetry to uv for dependency and build management [[29d35f5](https://github.com/NRWLDev/changelog-gen/commit/29d35f5e83bef0306d0f99244b7b500cf254362d)]

## v0.12.1 - 2024-09-06

### Bug fixes

- Handle rtoml issue with tables emitted before values. [[24724ca](https://github.com/NRWLDev/changelog-gen/commit/24724ca033d226f3cea83443a7f769a83823b962)]

## v0.12.0 - 2024-08-30

### Features and Improvements

- **Breaking** Drop bump-my-version dependency in favour of in house implementation. [[28](https://github.com/NRWLDev/changelog-gen/issues/28)] [[d74338a](https://github.com/NRWLDev/changelog-gen/commit/d74338ab84472a9439444968e7f7c187b690e91a)]
- **Breaking** Simplify commit type and semver configuration. [[35](https://github.com/NRWLDev/changelog-gen/issues/35)] [[cb76db2](https://github.com/NRWLDev/changelog-gen/commit/cb76db201be2f55daac22d16f0af0bd552788462)]
- **Breaking** Parse footers using regex, and support custom user parsers. [[36](https://github.com/NRWLDev/changelog-gen/issues/36)] [[80a335a](https://github.com/NRWLDev/changelog-gen/commit/80a335adb52679b76f6daec3e855818f5590db0f)]
- **Breaking** Support link parsers to extract information from footers and generate links and link text. [[37](https://github.com/NRWLDev/changelog-gen/issues/37)] [[c24f246](https://github.com/NRWLDev/changelog-gen/commit/c24f2461f5feac127e3caad56549226dc3de2eb3)]
- **Breaking** Update post process to generate link using a link parser, and build body with a jinja template. [[44](https://github.com/NRWLDev/changelog-gen/issues/44)] [[138c250](https://github.com/NRWLDev/changelog-gen/commit/138c250e8ea9adc2283f173319a249ebdcb523d8)]
- **Breaking** Separate footer parsing, information extraction and link generation. [[47](https://github.com/NRWLDev/changelog-gen/issues/47)] [[632634d](https://github.com/NRWLDev/changelog-gen/commit/632634db1ac59ca00e51ed079e5e48f77619f9e3)]
- Add support for PR ref extraction and links in changelog. [[33](https://github.com/NRWLDev/changelog-gen/issues/33)] [[b4eef73](https://github.com/NRWLDev/changelog-gen/commit/b4eef7368b3b6e2456fd2cc5cab886a49e1d6e7c)]
- Use jinja template to render changelog lines, support custom user templates. [[38](https://github.com/NRWLDev/changelog-gen/issues/38)] [[7aa9705](https://github.com/NRWLDev/changelog-gen/commit/7aa9705622e4dfa8607f0c0d0e98e1c401fabbec)]
- Output optional statistics for inclusion in release notes. [[46](https://github.com/NRWLDev/changelog-gen/issues/46)] [[5b38748](https://github.com/NRWLDev/changelog-gen/commit/5b387484021ac4e273758963fa1b4541857c3d13)]
- Add support for signed AWS4 requests for post process requests. [[49](https://github.com/NRWLDev/changelog-gen/issues/49)] [[d7961dc](https://github.com/NRWLDev/changelog-gen/commit/d7961dc34eb350f8fc5bc9f830af11306d846543)]
- Support special github scenarios via configuration [[50](https://github.com/NRWLDev/changelog-gen/issues/50)] [[69d5002](https://github.com/NRWLDev/changelog-gen/commit/69d50025c0e2a8fe2a43258f12c24c2115605df5)]

### Bug fixes

- Add github fixes footer support, and make footer lookups case insensitive [[6520681](https://github.com/NRWLDev/changelog-gen/commit/652068137176ae165b96e2722811110a8920602b)]

## v0.11.14 - 2024-08-16

### Features and Improvements

- Add support for github `closes #X` footer in commit messages to extract issue_ref. [[#27](https://github.com/NRWLDev/changelog-gen/issues/27)] [[cd577a5](https://github.com/NRWLDev/changelog-gen/commit/cd577a5b57e43af68a5ef5f73e0a33e7f5366f05)]
- Add support for arbitrary user configuration for hooks [[#29](https://github.com/NRWLDev/changelog-gen/issues/29)] [[d5f2987](https://github.com/NRWLDev/changelog-gen/commit/d5f2987fa58c04f8b5d837515c77d3c9897c0a86)]

## v0.11.13 - 2024-08-16

### Bug fixes

- Pass context object to hooks to expose output methods and configuration. [[bc37854](https://github.com/NRWLDev/changelog-gen/commit/bc37854c9fb4c81b8042ab5b8e0f1d7c4ff5bb26)]

## v0.11.12 - 2024-08-15

### Features and Improvements

- Support release hooks to perform actions when a release is made. [[#24](https://github.com/NRWLDev/changelog-gen/issues/24)] [[a99e669](https://github.com/NRWLDev/changelog-gen/commit/a99e6697890b63f0e32add1fceb1b3f062f9a3dc)]

## v0.11.11 - 2024-07-25

### Bug fixes

- Normalise commit types when matching to commit logs [[#22](https://github.com/NRWLDev/changelog-gen/issues/22)] [[a021c93](https://github.com/NRWLDev/changelog-gen/commit/a021c93a7cf2b78f220ba3149175222a0d0f3637)]

## v0.11.10 - 2024-07-24

### Bug fixes

- Fix toml rendering for config subcommand. [[45614f4](https://github.com/NRWLDev/changelog-gen/commit/45614f4aa4ac4879ff1412b3fefa4f95a59a4017)]

## v0.11.9 - 2024-07-24

### Bug fixes

- Support python3.8 in standard flows. [[f83df35](https://github.com/NRWLDev/changelog-gen/commit/f83df3596aca5ac02aa7c80208e31d17b0048dff)]

## v0.11.8 - 2024-07-15

### Features and Improvements

- Allow configuration of when to trigger a pre-release. [[#19](https://github.com/NRWLDev/changelog-gen/issues/19)] [[88fdb0f](https://github.com/NRWLDev/changelog-gen/commit/88fdb0f7c3cbee182680eae6d8a57aa1832bdcf3)]
- Add strict validation of parser/serialisers in line with SemVer 2.0.0 [[7417cfb](https://github.com/NRWLDev/changelog-gen/commit/7417cfbf636a26bc9b7c968053328273a953c6a0)]

## v0.11.7 - 2024-07-12

### Miscellaneous

- Add pypi metadata, classifiers etc. [[488d8cf](https://github.com/NRWLDev/changelog-gen/commit/488d8cfda84fc941df4ee4bc071001e2b77b37a5)]

## v0.11.6 - 2024-07-12

### Features and Improvements

- Provide stacktrace on error for -vvv. [[4faf03b](https://github.com/NRWLDev/changelog-gen/commit/4faf03b1059ef7a3b92c48db42ddacbd894b50ef)]

## v0.11.5 - 2024-07-12

### Bug fixes

- Add additional error handling. [[d0709e1](https://github.com/NRWLDev/changelog-gen/commit/d0709e116d8ca2055062786063dd9b6a4805e66b)]

## v0.11.4 - 2024-07-12

### Bug fixes

- Serialisers not serializers [[6b0474f](https://github.com/NRWLDev/changelog-gen/commit/6b0474ff97ec9e01b3fad846b8622db2b3d32ac3)]

## v0.11.3 - 2024-07-11

### Features and Improvements

- Move httpx to an optional extra for post-process support. [[5c3eb5a](https://github.com/NRWLDev/changelog-gen/commit/5c3eb5a25cb031688aec45c225289d326af6f04c)]

## v0.11.2 - 2024-07-11

### Features and Improvements

- Implement version bumping in house, prepare to deprecate bump-my-version. [[#14](https://github.com/NRWLDev/changelog-gen/issues/14)] [[6f5511c](https://github.com/NRWLDev/changelog-gen/commit/6f5511cf6bfd80ec4dd455c27b86e3c586241536)]

### Bug fixes

- Clean up modified files if failure occurs part way through. [[eacfad0](https://github.com/NRWLDev/changelog-gen/commit/eacfad08f00ba11e99ddecd2555e99337ef756d6)]
- Handle invalid patterns in file configuration [[f1c0a6b](https://github.com/NRWLDev/changelog-gen/commit/f1c0a6be5c426bcc14c6ccf2961744ad80f9aaf9)]

## v0.11.1 - 2024-07-09

### Bug fixes

- Search for tag directly over looping over all tags. [[dc10ba6](https://github.com/NRWLDev/changelog-gen/commit/dc10ba62c726f89aa917c98be0951ffe6f62e2a6)]

## v0.11.0 - 2024-07-09

### Features and Improvements

- **Breaking:** Use bump-my-version code directly, skip subprocess wrapped cli calls. [[851e225](https://github.com/NRWLDev/changelog-gen/commit/851e225c6e593a86521630c1efb7aca5ad4845f0)]

## v0.10.4 - 2024-07-09

### Features and Improvements

- Use `bump-my-version replace ...` to update version files and changelog in a single commit. [[dc27cb2](https://github.com/NRWLDev/changelog-gen/commit/dc27cb23bc387d97f34f447dd9d117f4dd0afac4)]

## v0.10.4 - 2024-07-09

### Features and Improvements

- Replace manual subprocess calls with GitPython usage. [[3cdab64](https://github.com/NRWLDev/changelog-gen/commit/3cdab64092857f357806a2c9078eba4a3b6db601)]

## v0.10.3 - 2024-07-08

### Bug fixes

- Clean up how bump-version error outputs are handled [[accdf8f](https://github.com/NRWLDev/changelog-gen/commit/accdf8ff376d7ea1620962b756c69c7bb223deb9)]

## v0.10.2 - 2024-07-08

### Features and Improvements

- Replace manual subprocess calls with GitPython usage. [[d5541bd](https://github.com/NRWLDev/changelog-gen/commit/d5541bd4487eafe5c4029d0275b4406bb0251faf)]

### Bug fixes

- Simplify conventional commit regex to capture all chars in description. [[441b1d5](https://github.com/NRWLDev/changelog-gen/commit/441b1d5bcffd3430a230b4aa273fd6d973a49cc8)]

## v0.10.1 - 2024-06-24

### Bug fixes

- Remove extras definitions [[76f0e02](https://github.com/NRWLDev/changelog-gen/commit/76f0e0257af857c61173dff524393e694756905d)]

## v0.10.0 - 2024-06-24

### Features and Improvements

- **Breaking:** Drop support for bump2version and remove deprecated code. [[6a65cb4](https://github.com/NRWLDev/changelog-gen/commit/6a65cb44a792fc0380fd180c0e00569a35b02868)]

## v0.9.13 - 2024-06-10

### Features and Improvements

- Add include-all flag to pick up non conventional commits. [[#7](https://github.com/NRWLDev/changelog-gen/issues/7)] [[8c8ccfd](https://github.com/NRWLDev/changelog-gen/commit/8c8ccfdabb8937f65b7cf24bcf4e3a412f89900c)]

## v0.9.12 - 2024-05-15

### Bug fixes

- Maintain changes from editor in final saved changelog. [[281d4be](https://github.com/NRWLDev/changelog-gen/commit/281d4bee9559c8a89b673dcc27b5bc9a95fb9ca5)]

## v0.9.11 - 2024-05-08

### Bug fixes

- Loosen httpx pin [[0c197cb](https://github.com/NRWLDev/changelog-gen/commit/0c197cba90073138f10592b22b8c7377feef1fc3)]

## v0.9.10 - 2024-05-01

### Bug fixes

- Fix test for update instead of overwrite of commit types. [[55a3ffa](https://github.com/NRWLDev/changelog-gen/commit/55a3ffaf89f627c7a94c2512ed8f60d12a8bc669)]

## v0.9.9 - 2024-04-18

### Features and Improvements

- Allow partial override of configured commit_types. [[#5](https://github.com/NRWLDev/changelog-gen/issues/5)] [[85259d0](https://github.com/NRWLDev/changelog-gen/commit/85259d08151770c0d564266d3b05ec2db35a4d53)]
- Add `changelog config` command to display current settings. [[55ac7b8](https://github.com/NRWLDev/changelog-gen/commit/55ac7b8d8e63459198adccd321197589a9bb1bd1)]

## v0.9.8 - 2024-04-12

### Features and Improvements

- Open changes in editor before confirmation, to allow modification. [[#1](https://github.com/NRWLDev/changelog-gen/issues/1)] [[a4e1449](https://github.com/NRWLDev/changelog-gen/commit/a4e1449bf44f370c671cc679d4bf9cfd75e68cbf)]
- Block generation if local/remote are out of sync. [[#2](https://github.com/NRWLDev/changelog-gen/issues/2)] [[c314b6b](https://github.com/NRWLDev/changelog-gen/commit/c314b6b8a32f4ce5c05869f0accd24bb4e6097f2)]

### Bug fixes

- Support `?` in commit log messages. [[#3](https://github.com/NRWLDev/changelog-gen/issues/3)] [[2d70733](https://github.com/NRWLDev/changelog-gen/commit/2d7073328aa18cb031a13c3c79f773db58500541)]

## v0.9.7 - 2024-04-08

### Miscellaneous

- Unlock typer version to 0.X [[2e25deb](https://github.com/NRWLDev/changelog-gen/commit/2e25deb902710343a0f85f40323762752eef4a45)]

## v0.9.6 - 2024-03-13

### Bug fixes

- Relax rtoml pin [[e7d3b1d](https://github.com/NRWLDev/changelog-gen/commit/e7d3b1d1484ce42673de2af2958cc8e93b978e23)]

## v0.9.5 - 2024-03-11

### Bug fixes

- Restore [[4c9114e](https://github.com/NRWLDev/changelog-gen/commit/4c9114e34d238359e687ffdbb7cee928df0f10da)]

## v0.9.4 - 2024-03-11

### Bug fixes

- Handle warning message from bump-my-version if setup.cfg exists [[a95fd80](https://github.com/NRWLDev/changelog-gen/commit/a95fd80d939985ab4b51a864676dda234e345d47)]

## v0.9.3 - 2024-03-08

### Bug fixes

- Support `-` in commit messages [[9608763](https://github.com/NRWLDev/changelog-gen/commit/9608763ff5f28447bbf11596a6494b001a107d8a)]

## v0.9.2 - 2024-03-08

### Bug fixes

- Clean up link generation format in MDWriter [[b46d2fe](https://github.com/NRWLDev/changelog-gen/commit/b46d2fe6fba5a170f25dffbf8697868d14a4e73e)]

## v0.9.1 - 2024-03-04

### Bug fixes

- Drop release notes support, fix issue in verbosity logging [[b8f9a7d](https://github.com/NRWLDev/changelog-gen/commit/b8f9a7dcef9263c9177be36a4996c97f2fe60a0b)]

## v0.9.0 - 2024-03-04

### Features and Improvements

- (`cli`) Add `migrate` command to generate toml from an existing setup.cfg. [[#85](https://github.com/NRWLDev/changelog-gen/issues/85)] [[c8acfef](https://github.com/NRWLDev/changelog-gen/commit/c8acfef69588ec282fbeca32ca0474cc0319c69b)]
- (`config`) Support string replacement over string.format [[#62](https://github.com/NRWLDev/changelog-gen/issues/62)] [[d83740a](https://github.com/NRWLDev/changelog-gen/commit/d83740a40028cbac93cd61c5b48c369d9b9d0fa9)]
- (`config`) Map custom sections to semver flags [[#68](https://github.com/NRWLDev/changelog-gen/issues/68)] [[3fd4c87](https://github.com/NRWLDev/changelog-gen/commit/3fd4c874b3a7e2bfb693668ccfbafda6acaff43a)]
- (`config`) Pull post_process request headers from configuration [[#70](https://github.com/NRWLDev/changelog-gen/issues/70)] [[7eb9def](https://github.com/NRWLDev/changelog-gen/commit/7eb9def5db6164ef3a343482ac2619ce7d6ab6ce)]
- (`config`) Deprecate config.sections and config.section_mapping, replace with config.type_headers [[#82](https://github.com/NRWLDev/changelog-gen/issues/82)] [[0809d65](https://github.com/NRWLDev/changelog-gen/commit/0809d65ed59d456ca0461d0c8916410efbed348a)]
- (`extractor`) Extract changelog messages from conventional commit logs [[#15](https://github.com/NRWLDev/changelog-gen/issues/15)] [[4ff5135](https://github.com/NRWLDev/changelog-gen/commit/4ff5135871b1aaf7044efb50ee05fd91292d3ecf)]
- (`extractor`) Extract authors footer from commit logs (edgy) [[#76](https://github.com/NRWLDev/changelog-gen/issues/76)] [[eed0a04](https://github.com/NRWLDev/changelog-gen/commit/eed0a04a6b99a8ee7b229948cff69068f5a3ae12)]
- (`post_process`) Add support for bearer auth flows i.e. Github [[#87](https://github.com/NRWLDev/changelog-gen/issues/87)] [[cf52e0b](https://github.com/NRWLDev/changelog-gen/commit/cf52e0b7354e9da9a44c1fed7f15a45c3ba82125)]
- (`writer`) Highlight breaking changes in changelog [[#73](https://github.com/NRWLDev/changelog-gen/issues/73)] [[bee2c5f](https://github.com/NRWLDev/changelog-gen/commit/bee2c5f16e4ed12dc029663243676fda85022d31)]
- (`writer`) Sort changes in changelog by breaking changes, scoped changes then by issue ref. (edgy) [[#75](https://github.com/NRWLDev/changelog-gen/issues/75)] [[21021dd](https://github.com/NRWLDev/changelog-gen/commit/21021dd6d2f2f3ed024f4fe16a0342202b795fd2)]
- (`writer`) include commit hash link if configured and conventional commits used [[#79](https://github.com/NRWLDev/changelog-gen/issues/79)] [[bad27bf](https://github.com/NRWLDev/changelog-gen/commit/bad27bf69086e099009c5b65bcd5c6ac7e0f2967)]
- Support prerelease flows when generating changelogs [[#47](https://github.com/NRWLDev/changelog-gen/issues/47)] [[abdef84](https://github.com/NRWLDev/changelog-gen/commit/abdef84d8153d2669374e313f644bd1fa03b74bc)]
- Support pyproject.toml as a configuration source. [[#55](https://github.com/NRWLDev/changelog-gen/issues/55)]
- Support bump [[#90](https://github.com/NRWLDev/changelog-gen/issues/90)] [[7916f6a](https://github.com/NRWLDev/changelog-gen/commit/7916f6a4f3683b7f37f4968e408071f2c9e13c43)]
- Add verbose logging to commands, and pass through to bumpversion. [[#95](https://github.com/NRWLDev/changelog-gen/issues/95)] [[c30bd1e](https://github.com/NRWLDev/changelog-gen/commit/c30bd1e48066915f071d18061bdfd310f69dc869)]
- Configure type, header and semver mappings in a single configuration option. [[#99](https://github.com/NRWLDev/changelog-gen/issues/99)] [[cb70873](https://github.com/NRWLDev/changelog-gen/commit/cb70873b5c5b8f1c7f0d44f75852b5e34b12dd34)]

### Bug fixes

- **Breaking:** Clean up dependencies, replace `requests` with `httpx` and `black` with `ruff
format`.  Upgrade lowest supported version of python to 3.9. [[#49](https://github.com/NRWLDev/changelog-gen/issues/49)]
- (`config`) Pull version string template from configuration [[#37](https://github.com/NRWLDev/changelog-gen/issues/37)] [[ea973ea](https://github.com/NRWLDev/changelog-gen/commit/ea973ea656ffb92e0260920612d93e3bfea6809f)]
- (`extractor`) Add clearer messaging for unsupported release_note types. [[#54](https://github.com/NRWLDev/changelog-gen/issues/54)] [[bdf4f32](https://github.com/NRWLDev/changelog-gen/commit/bdf4f32c616c00f4a9a2b45b8c14406b6694a7cd)]
- Update git commands to handle non version tags and repositories with no tags. [[#101](https://github.com/NRWLDev/changelog-gen/issues/101)] [[5292a79](https://github.com/NRWLDev/changelog-gen/commit/5292a790ed90d3211e16f408a4f195de8612be73)]
- Rollback changelog commit, if bumpversion release fails [[#36](https://github.com/NRWLDev/changelog-gen/issues/36)] [[985e0dc](https://github.com/NRWLDev/changelog-gen/commit/985e0dcc0941995ff5c74a3abf0f9608b65c0ea0)]
- Follow semver for 0.x releases. Breaking changes -> minor release. [[#50](https://github.com/NRWLDev/changelog-gen/issues/50)]
- Add support for reject-empty configuration flag. [[#52](https://github.com/NRWLDev/changelog-gen/issues/52)]
- Only run post_process commands, if changes were actually executed. [[#53](https://github.com/NRWLDev/changelog-gen/issues/53)]
- Support more conventional commit types out of the box [[#66](https://github.com/NRWLDev/changelog-gen/issues/66)] [[6aa93b2](https://github.com/NRWLDev/changelog-gen/commit/6aa93b2061c382b637c2ed2b3dfbfac75cc3f30c)]

## v0.8.1

### Bug fixes

- Introduce ruff instead of flake8 and pre-commit hooks. [[#48](https://github.com/NRWLDev/changelog-gen/issues/48)]

## v0.8.0

### Features and Improvements

- Handle sending data to APIs on release (e.g. jira). [[#42](https://github.com/NRWLDev/changelog-gen/issues/42)]
- Support python 3.7. [[#43](https://github.com/NRWLDev/changelog-gen/issues/43)]
- Allow negative command line parameters. [[#44](https://github.com/NRWLDev/changelog-gen/issues/44)]
- Add the date with the release version. [[#45](https://github.com/NRWLDev/changelog-gen/issues/45)]

### Bug fixes

- Fix release version string. [[#38](https://github.com/NRWLDev/changelog-gen/issues/38)]
- Fix link generation and old links in changelog file. [[#40](https://github.com/NRWLDev/changelog-gen/issues/40)]

## v0.7.0

### Features and Improvements

- Support vX.Y.Z style tags (bumpversion default) [[#37](https://github.com/NRWLDev/changelog-gen/issues/37)]

## v0.6.0

### Features and Improvements

- Support custom changelog headers. [[#32](https://github.com/NRWLDev/changelog-gen/issues/32)]

## v0.5.1

### Bug fixes

- Render RST links when performing a dry-run. [[#30](https://github.com/NRWLDev/changelog-gen/issues/30)]

## v0.5.0

### Features and Improvements

- Allow configuration of an issue url to create links in CHANGELOG. [[#28](https://github.com/NRWLDev/changelog-gen/issues/28)]

## v0.4.0

### Features and Improvements

- Add ability to restrict which branches command can run in, and to fail on dirty branch. [[#11](https://github.com/NRWLDev/changelog-gen/issues/11)]
- Allow configuration of release note suffix to changelog section mapping. [[#19](https://github.com/NRWLDev/changelog-gen/issues/19)]

### Bug fixes

- Commit configuration was ignored. Fixed cli to use configured value. [[#24](https://github.com/NRWLDev/changelog-gen/issues/24)]

## v0.3.0

### Features and Improvements

- Add in --release flag to trigger tagging the release. [[#12](https://github.com/NRWLDev/changelog-gen/issues/12)]
- Add in --version-tag flag to skip auto generation of the version tag. [[#13](https://github.com/NRWLDev/changelog-gen/issues/13)]
- Support configuration via setup.cfg [[#14](https://github.com/NRWLDev/changelog-gen/issues/14)]
- Introduce a method to detect breaking changes. [[#16](https://github.com/NRWLDev/changelog-gen/issues/16)]

## v0.2.3

### Bug fixes

- Add in tests [[#8](https://github.com/NRWLDev/changelog-gen/issues/8)]

## v0.2.2

### Bug fixes

- Fix missing import in cli.command [[#5](https://github.com/NRWLDev/changelog-gen/issues/5)]

## v0.2.1

### Bug fixes

- Raise errors from internal classes, don't use click.echo() [[#4](https://github.com/NRWLDev/changelog-gen/issues/4)]

- Update changelog line format to include issue number at the end. [[#7](https://github.com/NRWLDev/changelog-gen/issues/7)]

## v0.2.0

### Features and Improvements

- Bump the version of the library after writing changelog. [[#6](https://github.com/NRWLDev/changelog-gen/issues/6)]

## v0.1.0

### Features and Improvements

- Add in dependency on bumpversion to get current and new version tags. [[#3](https://github.com/NRWLDev/changelog-gen/issues/3)]

## v0.0.11

### Features and Improvements

- Use ConventionalCommit style endings. [[#1](https://github.com/NRWLDev/changelog-gen/issues/1)]
