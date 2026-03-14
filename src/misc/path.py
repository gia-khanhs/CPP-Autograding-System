from pathlib import Path
from typing import Literal, overload

def get_subpaths(parent_dir: Path) -> list[Path]:
    subpaths = [path
                for path in parent_dir.iterdir()]
    
    return subpaths


def get_subfolders(parent_dir: Path) -> list[Path]:
    subfolders = [folder
                  for folder in parent_dir.iterdir()
                  if folder.is_dir()]
    
    return subfolders


def get_subfiles(parent_dir: Path) -> list[Path]:
    subfiles = [file
                for file in parent_dir.iterdir()
                if file.is_file()]

    return subfiles

@overload
def get_files_of_type(parent_dir: Path, file_extension: str, only: Literal[True]) -> Path: ...
@overload
def get_files_of_type(parent_dir: Path, file_extension: str, only: Literal[False]) -> list[Path]: ...

def get_files_of_type(parent_dir: Path, file_extension: str, only: bool = False) -> Path | list[Path]:
    files = [file
             for file in parent_dir.glob(f"*.{file_extension}")
             if file.is_file()]
    
    if len(files) != 1:
        raise FileExistsError(f"Make sure there is exactly one .{file_extension} file in the folder!")
    else:
        files = files[0]

    return files


