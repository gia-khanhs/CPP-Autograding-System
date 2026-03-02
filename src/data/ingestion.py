from pathlib import Path

from config.paths import RAW_DATA_DIR
from src.cpp.compiler import Compiler


def get_subfolders(parent_dir: Path) -> list[Path]:
    subfolders = [folder
                  for folder in parent_dir.iterdir()
                  if folder.is_dir()]
    
    return subfolders


class CodeSubmission:
    def __init__(self, directory: Path, compiler = Compiler) -> None:
        self.directory = directory
        self.raw_source_directory = directory / 'main.cpp'
        self.raw_program = compiler(self.raw_source_directory)


def get_all_submissions() -> list[CodeSubmission]:
    problem_folders = get_subfolders(RAW_DATA_DIR)

    submissions = [CodeSubmission(submission_i)
                for submission_i in problem_folders]
    
    return submissions