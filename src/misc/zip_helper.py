import os
from pathlib import Path
import zipfile

from config.paths import EXTRACTED_SUBMISSION_FOLDER

from .path import get_files_of_type

class ZipExtractor:
    flag_extension = ".extracted_flag"

    def __init__(self, zip_path: Path) -> None:
        self.zip_path = zip_path

    def create_flag(self, destination: Path) -> None:
        zip_flag = open(destination / ZipExtractor.flag_extension, "w")
        zip_flag.close()

    def is_extracted(self, destination: Path) -> bool:
        try:
            get_files_of_type(destination, ZipExtractor.flag_extension, only=True)
            return True
        except:
            return False
    
    def extract(self, destination: Path) -> None:
        if not os.path.exists(destination):
            os.makedirs(destination)

        with zipfile.ZipFile(self.zip_path, "r") as zip_ref:
            extracted_folder = destination / EXTRACTED_SUBMISSION_FOLDER
            zip_ref.extractall(extracted_folder)

    def extract_if_needed(self, destination: Path) -> bool:
        extracted_folder = destination / EXTRACTED_SUBMISSION_FOLDER

        if self.is_extracted(destination):
            return False
        else:
            self.extract(destination)
            self.create_flag(destination)
            return True
