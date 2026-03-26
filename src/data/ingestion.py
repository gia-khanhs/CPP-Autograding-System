from pathlib import Path
from typing import Optional, cast


from config.paths import RAW_DATA_DIR, EXTRACTED_SUBMISSION_MASTER_FOLDER

from ..misc.path import get_files_of_type, get_subfolders, get_only_subfolder
from ..misc.pdf_helper import read_pdf
from ..misc.archive_helper import ArchiveExtractor, get_only_archive
from ..misc.debug import logged
from ..cpp.program import Script, has_main

from .structures import Course, Week, ProblemSet, Problem, SubmissionSet, Submission


class Ingestor[T]:
    def ingest(self) -> T:
        ...


class ProblemSetIngestor(Ingestor[ProblemSet]):
    def __init__(self, folder_path: Path) -> None:
        self.folder_path = folder_path

    def get_pdf_path(self) -> Path:
        problem_set_pdf = get_files_of_type(self.folder_path, "pdf", only=True)

        return problem_set_pdf
        
    def ingest(self) -> ProblemSet:
        pdf_path = self.get_pdf_path()
        text_content = read_pdf(pdf_path)

        return ProblemSet(pdf_path, text_content)
    
class SubmissionIngestor(Ingestor[list[Submission]]):
    def __init__(self, submission_set: SubmissionSet) -> None:
        self.submission_set = submission_set

    def find_main_script(self, folder_path: Path) -> Optional[Path]:
        folder_queue = [folder_path]

        while len(folder_queue):
            search_folder = folder_queue[0]
            folder_queue.pop(0)

            cpp_paths = get_files_of_type(search_folder, "cpp", False)
            for cpp_path in cpp_paths:
                if has_main(cpp_path):
                    return cpp_path

            subfolders = get_subfolders(search_folder)
            folder_queue = folder_queue + subfolders

        return None

    def ingest(self) -> list[Submission]:
        submissions = []

        submission_folders = get_subfolders(self.submission_set.folder_path)
        for submission_folder in submission_folders:
            main_path = self.find_main_script(submission_folder)
            
            submission = Submission(submission_folder, Script(main_path, processing_includes=True))
            submissions.append(submission)

        return submissions

class SubmissionSetIngestor(Ingestor[list[SubmissionSet]]):
    def __init__(self, folder_path) -> None:
        self.folder_path = folder_path

    def get_master_archive(self) -> Path:
        master_archive_path = get_only_archive(self.folder_path)

        return master_archive_path
        
    def get_master_folder(self) -> Path:
        master_folder = self.folder_path / EXTRACTED_SUBMISSION_MASTER_FOLDER
        return master_folder

    def extract_master_archive(self) -> bool:
        master_archive_path = self.get_master_archive()

        master_extractor = ArchiveExtractor(master_archive_path)
        extracted_path = self.get_master_folder()
        result = master_extractor.extract_if_needed(extracted_path)
        return result

    def get_submission_set_archive_folders(self) -> list[Path]:
        master_folder = self.get_master_folder()
        submission_set_archive_folders = get_subfolders(master_folder)

        return submission_set_archive_folders
    
    def get_submission_set_archives(self) -> list[Path]:
        submission_set_archive_folders = self.get_submission_set_archive_folders()
        submission_set_archives = []
        for folder in submission_set_archive_folders:
            archive = get_only_archive(folder)
            submission_set_archives.append(archive)

        return submission_set_archives

    def extract_submission_set_archives(self) -> None:
        submission_set_archive_folders = self.get_submission_set_archive_folders()
        submission_set_archives = self.get_submission_set_archives()

        for destination, archive in zip(submission_set_archive_folders, submission_set_archives):
            submission_extractor = ArchiveExtractor(archive)
            submission_extractor.extract_if_needed(destination)

    def get_submission_set_folders(self) -> list[Path]:
        submission_set_folders = []
        submission_set_archive_folders = self.get_submission_set_archive_folders()

        for submission_set_folder in submission_set_archive_folders:
            extracted_folder = None
            try:
                extracted_folder = get_only_subfolder(submission_set_folder)
            except:
                extracted_folder = submission_set_folder

            submission_set_folders.append(extracted_folder)

        return submission_set_folders

    def ingest(self) -> list[SubmissionSet]:
        submission_sets = []

        self.extract_master_archive()
        archive_folders = self.get_submission_set_archive_folders()
        self.extract_submission_set_archives()
        submission_set_folders = self.get_submission_set_folders()

        for submission_set_folder, archive_folder in zip(submission_set_folders, archive_folders):
            submission_set = SubmissionSet(submission_set_folder, archive_folder)
            submission_set.submissions = SubmissionIngestor(submission_set).ingest()
            submission_sets.append(submission_set)

        return submission_sets


class WeekIngestor(Ingestor[Week]):
    def __init__(self, folder_path: Path) -> None:
        self.folder_path = folder_path

    def ingest(self) -> Week:
        problem_set: Optional[ProblemSet] = ProblemSetIngestor(self.folder_path).ingest()
        submission_set: list[SubmissionSet] = SubmissionSetIngestor(self.folder_path).ingest()

        return Week(self.folder_path, problem_set, submission_set)


class CourseIngestor(Ingestor[Course]):
    def __init__(self, folder_path: Path = RAW_DATA_DIR) -> None:
        self.folder_path = folder_path
        
    def ingest(self) -> Course:
        weeks: list[Week] = []

        week_paths = get_subfolders(self.folder_path)
        for week_path in week_paths:
            week = WeekIngestor(folder_path=week_path).ingest()
            weeks.append(week)

        return Course(self.folder_path, weeks)

