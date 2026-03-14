from pathlib import Path
from typing import Optional, cast


import pymupdf
import pymupdf4llm


from config.paths import RAW_DATA_DIR, ITERIM_DATA_DIR
from config.paths import EXTRACTED_SUBMISSION_FOLDER

from ..misc.logger import logged
from ..misc.path import get_files_of_type, get_subfolders
from ..misc.pdf_helper import read_pdf
from ..misc.zip_helper import ZipExtractor

from .structures import Course, Week, ProblemSet, Submission


class ProblemSetLoader:
    def __init__(self, folder_path: Path) -> None:
        self.folder_path = folder_path

    def get_pdf_path(self) -> Path:
        problem_set_pdf = get_files_of_type(self.folder_path, "pdf", only=True)
        
        assert(type(problem_set_pdf) == Path)
        return problem_set_pdf

    def load(self) -> ProblemSet:
        pdf_path = self.get_pdf_path()
        text_content = read_pdf(pdf_path)

        return ProblemSet(pdf_path, text_content)


class SubmissionLoader:
    def __init__(self, folder_path) -> None:
        self.folder_path = folder_path

    def get_zip_path(self) -> Path:
        submission_zip_path = get_files_of_type(self.folder_path, "zip", only=True)

        assert(type(submission_zip_path) == Path)
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


class WeekLoader:
    def __init__(self, folder_path: Path) -> None:
        self.folder_path = folder_path

    def load(self):
        problem_set: Optional[ProblemSet] = ProblemSetLoader(self.folder_path).load()
        submissions: list[Submission] = SubmissionLoader(self.folder_path).load()

        return Week(self.folder_path, problem_set, submissions)


class CourseLoader:
    def __init__(self, folder_path: Path = RAW_DATA_DIR) -> None:
        self.folder_path = folder_path
        
    def load(self):
        weeks: list[Week] = []

        week_paths = get_subfolders(self.folder_path)
        for week_path in week_paths:
            week = WeekLoader(folder_path=week_path).load()
            weeks.append(week)

        return Course(self.folder_path, weeks)


class problematic:
    def __init__(self, pdf_path: Path) -> None:
        self.pdf_path = pdf_path


    @logged
    def get_md_text(self) -> str:
        pdf_doc = pymupdf.open(self.pdf_path)

        full_content = pymupdf4llm.to_markdown(pdf_doc,
            header=False, footer=False, use_ocr=False, sort=True)
        full_content = cast(str, full_content)
        
        pdf_doc.close()

        return full_content.strip()

    
    def convert_to_md(self, output_path: Optional[Path] = None) -> Path:
        if output_path == None:
            weekly_folder_path = self.pdf_path.parent
            weekly_folder_name = weekly_folder_path.name

            output_path = ITERIM_DATA_DIR / weekly_folder_name / "problem_set.md"

        text_content = self.get_md_text()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text_content, encoding="utf-8")

        return output_path


