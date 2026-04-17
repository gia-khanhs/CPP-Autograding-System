from pathlib import Path
from typing import Optional

from .state import AppState
from .logger import (
    app_log,
    load_page_logged,
    autocorrection_page_logged,
    grading_page_logged,
)
from ..data.structures import Course
from ..data.pipeline import DataPipeline
from ..grading.correction import CourseCorrector


class AppBackend:
    def __init__(self) -> None:
        self.state = AppState()

    def load_data(self, raw_dir: Path, processed_dir: Path) -> Course:
        self.state._raw_dir = raw_dir
        self.state._processed_dir = processed_dir
        self.state._loaded_course = DataPipeline(raw_dir, processed_dir).get()
        return self.state._loaded_course

    def correct_code(self, corrected_dir: Path) -> None:
        self.state._corrected_dir = corrected_dir
        
        if self.state._loaded_course is None:
            app_log("autocorrection", "No course data loaded yet.")
            return
        

        CourseCorrector(self.state._loaded_course,
                        self.state._processed_dir,
                        self.state._corrected_dir
                        ).correct()

    @grading_page_logged
    def grade(self) -> None:
        if self.state._loaded_course is None:
            app_log("grading", "No course data loaded yet.")
            return

        app_log("grading", "Grading has not been implemented yet.")

    @property
    def loaded_course(self) -> Optional[Course]:
        return self.state._loaded_course

    @loaded_course.setter
    def loaded_course(self, course: Optional[Course]) -> None:
        self.state._loaded_course = course

    @property
    def raw_dir(self) -> Optional[Path]:
        return self.state._raw_dir

    @raw_dir.setter
    def raw_dir(self, dir: Path) -> None:
        self.state._raw_dir = dir

    @property
    def processed_dir(self) -> Optional[Path]:
        return self.state._processed_dir

    @processed_dir.setter
    def processed_dir(self, dir: Path) -> None:
        self.state._processed_dir = dir

    @property
    def corrected_dir(self) -> Optional[Path]:
        return self.state._corrected_dir

    @corrected_dir.setter
    def corrected_dir(self, dir: Path) -> None:
        self.state._corrected_dir = dir