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
