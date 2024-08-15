import re
from pathlib import Path

import pdoc


def hook(current, new) -> list[str]:  # noqa: D103, ANN001, ARG001
    output_dir = Path("./docs")
    modules = ["changelog_gen"]
    context = pdoc.Context()

    modules = [pdoc.Module(mod, context=context) for mod in modules]
    pdoc.link_inheritance(context)

    def recursive_mds(mod: pdoc.Module) -> pdoc.Module:
        yield mod
        for submod in mod.submodules():
            yield from recursive_mds(submod)

    for mod in modules:
        for module in recursive_mds(mod):
            path = re.sub(r"\.html$", ".md", module.url())
            out = output_dir / path
            out.parent.mkdir(exist_ok=True, parents=True)
            with out.open("w") as f:
                f.write(module.text())


if __name__ == "__main__":
    hook("a", "b")
