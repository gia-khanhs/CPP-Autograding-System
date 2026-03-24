from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


from src.cpp.program import Script


@dataclass
class Problem:
    problem_title: str
    problem_statement: str


@dataclass
class ProblemSet:
    pdf_path: Optional[Path]
    text_content: Optional[str]
    problems: list[Problem] = field(default_factory=list)


@dataclass
class Submission:
    folder_path: Path
    script: Script

@dataclass
class SubmissionSet:
    folder_path: Path
    archive_folder: Optional[Path]
    submissions: list[Submission] = field(default_factory=list)


@dataclass
class Week:
    folder_path: Path
    problem_set: ProblemSet
    submission_set: list[SubmissionSet] = field(default_factory=list)


@dataclass
class Course:
    folder_path: Path
    weeks: list[Week] = field(default_factory=list)