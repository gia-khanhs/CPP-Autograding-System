from pathlib import Path
from typing import Optional, cast


from config.paths import RAW_DATA_DIR

from ..misc.path import get_files_of_type, get_subfolders
from ..misc.pdf_helper import read_pdf
from ..misc.zip_helper import ZipExtractor

from .structures import Course, Week, ProblemSet, Submission


class Loader[T]:
    def load(self) -> T:
        ...


class ProblemSetLoader(Loader[ProblemSet]):
    def __init__(self, folder_path: Path) -> None:
        self.folder_path = folder_path

    def get_pdf_path(self) -> Path:
        problem_set_pdf = get_files_of_type(self.folder_path, "pdf", only=True)

        return problem_set_pdf
        
    def load(self) -> ProblemSet:
        pdf_path = self.get_pdf_path()
        text_content = read_pdf(pdf_path)

        return ProblemSet(pdf_path, text_content)


class SubmissionLoader(Loader[list[Submission]]):
    def __init__(self, folder_path) -> None:
        self.folder_path = folder_path

    def get_zip_path(self) -> Path:
        submission_zip_path = get_files_of_type(self.folder_path, "zip", only=True)

        return submission_zip_path
        
    def extract_zip(self, zip_path: Path) -> None:
        zip_extractor = ZipExtractor(zip_path)
        zip_extractor.extract_if_needed(self.folder_path)

    def load(self) -> list[Submission]:
        submissions = []

        submission_zip_path = self.get_zip_path()
        self.extract_zip(submission_zip_path)

        subfolders = get_subfolders(self.folder_path)
        for subfolder in subfolders:
            submission = Submission(subfolder)
            submissions.append(submission)
        
        return submissions


class WeekLoader(Loader[Week]):
    def __init__(self, folder_path: Path) -> None:
        self.folder_path = folder_path

    def load(self):
        problem_set: Optional[ProblemSet] = ProblemSetLoader(self.folder_path).load()
        submissions: list[Submission] = SubmissionLoader(self.folder_path).load()

        return Week(self.folder_path, problem_set, submissions)


class CourseLoader(Loader[Course]):
    def __init__(self, folder_path: Path = RAW_DATA_DIR) -> None:
        self.folder_path = folder_path
        
    def load(self):
        weeks: list[Week] = []

        week_paths = get_subfolders(self.folder_path)
        for week_path in week_paths:
            week = WeekLoader(folder_path=week_path).load()
            weeks.append(week)

        return Course(self.folder_path, weeks)

