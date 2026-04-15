from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json


from src.cpp.program import Script


@dataclass
class Problem:
    problem_title: str
    problem_statement: str
    type: str

    @property
    def title(self) -> Optional[str]:
        return self.problem_title

    @property
    def statement(self) -> Optional[str]:
        return self.problem_statement

@dataclass
class ProblemSet:
    pdf_path: Optional[Path]
    text_content: Optional[str]
    problems: list[Problem] = field(default_factory=list)


@dataclass
class Submission:
    folder_path: Path
    _script: Optional[Script]

    @property
    def script(self) -> Script:
        if self._script is None:
            return Script(None, False)
        
        return self._script

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

@dataclass
class LazyProblem:
    json_path: Path
    _problem: Optional[Problem] = field(default=None, init=False, repr=False)

    def get_problem_dict(self):
        problem_dict = None
        with open(self.json_path, "r", encoding="utf-8") as save_file:
            problem_dict = save_file.read()
            problem_dict = json.loads(problem_dict)

            save_file.close()

        return problem_dict
    

    def _load(self) -> Problem:
        if self._problem is None:
            problem_dict = self.get_problem_dict()

            self._problem = Problem(**problem_dict)

        return self._problem
    

    @property
    def problem_title(self) -> str:
        return self._load().problem_title
    
    @property
    def problem_statement(self) -> str:
        return self._load().problem_statement
    
    @property
    def type(self) -> str:
        return self._load().type
            
@dataclass
class LazySubmission:
    main_file: Path
    _submission: Optional[Submission] = field(default=None, init=False, repr=False)

    def _load(self) -> Submission:
        if self._submission is None:
            folder_path = self.main_file.parent

            script = Script(self.main_file, False)
            submission = Submission(folder_path, script)

            self._submission = submission

        return self._submission

    @property
    def folder_path(self) -> Path:
        return self._load().folder_path

    @property
    def script(self) -> Script:
        return self._load().script