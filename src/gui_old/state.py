from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..data.pipeline import DataPipeline
from ..data.structures import Course
from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR, CORRECTED_CODE_DIR, OUTPUT_DIR

@dataclass
class AppState:
    _raw_dir: Path = RAW_DATA_DIR
    _processed_dir: Path = PROCESSED_DATA_DIR
    _corrected_dir: Path = CORRECTED_CODE_DIR
    _output_dir: Path = OUTPUT_DIR
    _loaded_course: Optional[Course] = None