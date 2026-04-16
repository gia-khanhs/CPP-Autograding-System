from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .state import AppState
from ..data.structures import Course
from ..data.pipeline import DataPipeline


class AppBackend:
    def __init__(self) -> None:
        self.state = AppState()
        
    def load_data(self, raw_dir: Path, processed_dir: Path) -> Course:
        self.state._raw_dir = raw_dir
        self.state._processed_dir = processed_dir
        self.state._loaded_course = DataPipeline(raw_dir, processed_dir).get()
        return self.state._loaded_course
    
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