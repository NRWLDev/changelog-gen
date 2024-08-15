# Hooks

During the release process, some internal hooks to generate the changelog
entry, as well as bumping version files are run, during this step custom hooks
can be run as well if there are other steps you need to run as part of a
release. A good example of this could be regenerating automated docstring
documentation.

The hook function format is relatively simple, it takes in the current and new
version objects, and must return a list of the files, if any, that were
modified. The version objects are provided to allow using the values as
parameters if required.

```python
from changelog_gen.version import Version

def my_hook(current: Version, new: Version) -> list[str]:
    # Perform desired operation

    return ["/path/to/file1", "/path/to/file2"]
```

See
[hooks](https://nrwldev.github.io/changelog-gen/configuration/#hooks)
for details on configurating custom hooks.


## Example

Here is a full example used in another project to generate `.md` files from
docstrings, this will output a `module_name/`  directory in the local `docs/`
directory containing all modules and submodule `.md` files.


```python
import re
from pathlib import Path

import pdoc
from changelog_gen import Version


def hook(_current: Version, _new: Version) -> list[str]:
    output_dir = Path("./docs")
    modules = ["module_name"]
    context = pdoc.Context()

    modules = [pdoc.Module(mod, context=context) for mod in modules]
    pdoc.link_inheritance(context)

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
            paths.append(str(out))

    return paths
```
