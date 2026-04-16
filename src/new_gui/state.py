from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..data.pipeline import DataPipeline
from ..data.structures import Course

@dataclass
class AppState:
    _raw_dir: Optional[Path] = None
    _processed_dir: Optional[Path] = None
    _corrected_dir: Optional[Path] = None
    _loaded_course: Optional[Course] = None