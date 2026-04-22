from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from config.paths import CORRECTED_CODE_DIR, GRADE_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from ..data.structures import Course


@dataclass
class RunConfig:
    raw_dir: Path = RAW_DATA_DIR
    processed_dir: Path = PROCESSED_DATA_DIR
    corrected_dir: Path = CORRECTED_CODE_DIR
    grade_dir: Path = GRADE_DIR
    run_autocorrection: bool = True
    selected_week_names: list[str] = field(default_factory=list)


@dataclass
class ProgressUpdate:
    stage: str
    message: str = ""
    week_name: str = ""
    completed_weeks: int = 0
    total_weeks: int = 0
    failures: int = 0


@dataclass
class FailureItem:
    week_name: str
    submitter: str
    problem_label: str
    stage: str
    reason: str
    path: str = ""


@dataclass
class WeekResult:
    week_name: str
    score_df: pd.DataFrame
    output_path: Path
    failures: list[FailureItem] = field(default_factory=list)


@dataclass
class BatchRunResult:
    config: RunConfig
    week_results: list[WeekResult] = field(default_factory=list)
    failures: list[FailureItem] = field(default_factory=list)


@dataclass
class AppState:
    raw_dir: Path = RAW_DATA_DIR
    processed_dir: Path = PROCESSED_DATA_DIR
    corrected_dir: Path = CORRECTED_CODE_DIR
    grade_dir: Path = GRADE_DIR
    loaded_course: Optional[Course] = None
    last_run_result: Optional[BatchRunResult] = None
