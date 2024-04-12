from __future__ import annotations

import os
from pathlib import Path

from changelog_gen.writer import Extension


def detect_extension() -> Extension | None:
    """Detect existing CHANGELOG file extension."""
    for ext in Extension:
        if Path(f"CHANGELOG.{ext.value}").exists():
            return ext
    return None


def get_editor() -> str:
    """Return the user's preferred visual editor."""
    for key in ["VISUAL", "EDITOR"]:
        editor = os.environ.get(key, None)
        if editor:
            return editor
    return "vi"
