# Hooks

During the release process, some internal hooks to generate the changelog
entry, as well as bumping version files are run, during this step custom hooks
can be run as well if there are other steps you need to run as part of a
release. A good example of this could be regenerating automated docstring
documentation.

The hook function format is relatively simple, it takes in the current context,
as well as the new version string, and must return a list of the
files, if any, that were modified. The new version is provided to allow
using the values as parameters if required. The context object provides
messaging ability as well as access to the current config object.

```python
from changelog_gen.context import Context

def my_hook(context: Context, new: str) -> list[str]:
    # Perform desired operation

    context.error("Display something to the user.")
    return ["/path/to/file1", "/path/to/file2"]
```
See
[hooks](https://nrwldev.github.io/changelog-gen/configuration/#hooks)
for details on configuring custom hooks.


## Context

The context object provides access to the current configuration
`context.config` as well as to convenience methods for outputting information,
based on current verbosity settings.

* error: Always display
* warning: Display for -v verbosity or higher
* info: Display for -vv verbosity or higher
* debug: Display for -vvv verbosity or higher

The above methods accept a % format string, and `*args`. i.e.
`context.error("Hello, %s", "world")`.  To access the current version, extract
it from `context.config.current_version`.

### Configuration

Custom configuration can be accessed  with `context.config.custom`. This is a
dictionary containing all values defined in `[tool.changelog_gen.custom]`.  See
[custom](https://nrwldev.github.io/changelog-gen/configuration/#custom) for
details on providing custom configuration.

## Example

Here is a full example used in another project to generate `.md` files from
docstrings (using pdoc3 library), this will output a `module_name/`  directory
in the local `docs/` directory containing all modules and submodule `.md`
files.


```python
import re
from pathlib import Path

import pdoc
from changelog_gen.context import Context


def hook(context: Context, _new: str) -> list[str]:
    output_dir = Path("./docs")
    modules = ["module_name"]
    pcontext = pdoc.Context()

    modules = [pdoc.Module(mod, context=pcontext) for mod in modules]
    pdoc.link_inheritance(pcontext)

    def recursive_mds(mod: pdoc.Module) -> pdoc.Module:
        yield mod
        for submod in mod.submodules():
            yield from recursive_mds(submod)

    paths = []

    for mod in modules:
        for module in recursive_mds(mod):
            path = re.sub(r"\.html$", ".md", module.url())
            out = output_dir / path
            out.parent.mkdir(exist_ok=True, parents=True)
            with out.open("w") as f:
                f.write(module.text())
            context.info("Generated documentation for %s module", module.name)
            paths.append(str(out))

    return paths
```
