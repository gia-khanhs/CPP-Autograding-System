from pathlib import Path
import shutil
import os


import rarfile
import zipfile


from src.misc.path import get_files_of_type
from src.misc.logger import logged


def get_only_archive(folder: Path) -> Path:
    zips = get_files_of_type(folder, "zip", only=False)
    rars = get_files_of_type(folder, "rar", only=False)

    archive_count = len(zips) + len(rars)
    if archive_count != 1:
        raise FileExistsError(f"Make sure there is exactly one .zip or .rar file in the folder!")

    if len(zips):
        return zips[0]
    else:
        return rars[0]



class ExtractorTool:
    flag_extension: str
    def extract(self, archive_path: Path, destination: Path) -> None:...


class RarExtractorTool(ExtractorTool):
    flag_extension = ".rar_extracted"

    def check_backend(self) -> bool:
        if shutil.which("unrar"):
            rarfile.UNRAR_TOOL = "unrar"
            return True
        elif shutil.which("7z"):
            rarfile.UNRAR_TOOL = "7z"
            return True
            
        return False

    def __init__(self) -> None:
        if not self.check_backend():
            raise ImportError("Missing \"unrar\" command-line tool, please install it beforehand!" \
            "If it is installed, please add WinRAR folder to your System PATH!")


    def extract(self, archive_path: Path, destination: Path) -> None:
        if not os.path.exists(destination):
            os.makedirs(destination)

        with rarfile.RarFile(archive_path, "r") as rar_ref:
            rar_ref.extractall(destination)


class ZipExtractorTool(ExtractorTool):
    flag_extension = ".zip_extracted"

    def __init__(self) -> None:
        return None

    def extract(self, archive_path: Path, destination: Path) -> None:
        if not os.path.exists(destination):
            os.makedirs(destination)

        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(destination)
            print(zip_ref.namelist())


class ArchiveExtractor:
    __zip_extractor = ZipExtractorTool()
    __rar_extractor = RarExtractorTool()
    __extractors = {".zip": __zip_extractor, ".rar": __rar_extractor}

    def reinit(self, archive_path: Path) -> None:
        self.__archive_path = archive_path

        archive_extension = archive_path.suffix
        self.extractor = ArchiveExtractor.__extractors[archive_extension]
        
    def __init__(self, archive_path: Path) -> None:
        self.reinit(archive_path)
    
    def get_flag_path(self, destination: Path) -> Path:
        archive_name = self.__archive_path.name

        flag_path = destination / archive_name
        flag_path = flag_path.with_suffix(self.extractor.flag_extension)

        return flag_path

    def create_extrated_flag(self, destination: Path) -> None:
        flag_path = self.get_flag_path(destination)
        with open(flag_path, "w") as flag_file:
            flag_file.close()

    def check_extracted_flag(self, destination: Path) -> bool:
        flag_path = self.get_flag_path(destination)
        return flag_path.is_file()
    
    def delete_extracted_path(self, destination: Path) -> None:
        flag_path = self.get_flag_path(destination)
        
        if os.path.exists(flag_path):
            os.remove(flag_path)

    def extract(self, destination: Path) -> None:
        self.extractor.extract(self.__archive_path, destination)
        self.create_extrated_flag(destination)

    def extract_if_needed(self, destination: Path) -> bool:
        if self.check_extracted_flag(destination):
            return False
        else:
            self.extract(destination)
            return True