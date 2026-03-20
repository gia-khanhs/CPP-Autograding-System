from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

@dataclass
class Problem:
    problem_title: str
    problem_statement: str


@dataclass
class ProblemSet:
    pdf_path: Path
    text_content: str = ""
    problems: list[Problem] = field(default_factory=list)


@dataclass
class Submission:
    folder_path: Path
    

@dataclass
class SubmissionSet:
    folder_path: Path
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