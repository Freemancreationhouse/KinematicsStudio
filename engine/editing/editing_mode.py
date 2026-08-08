from __future__ import annotations

from enum import Enum


class EditingMode(str, Enum):
    """Supported geometry editing session modes."""

    SELECT = "Select"
    DIRECT = "Direct"
    SKETCH = "Sketch"
    FEATURE = "Feature"
    AI_ASSISTED = "AI Assisted"
