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

def get_only_subfolder(parent_dir: Path) -> Path:
    subfolders = get_subfolders(parent_dir)

    if len(subfolders) != 1:
        raise FileExistsError("There are more than one folder in the directory."
        "Expected one.")
    
    return subfolders[0]

@overload
def get_files_of_type(parent_dir: Path, file_extension: str, only: Literal[True]) -> Path: ...
@overload
def get_files_of_type(parent_dir: Path, file_extension: str, only: Literal[False]) -> list[Path]: ...

def get_files_of_type(parent_dir: Path, file_extension: str, only: bool = False) -> Path | list[Path]:
    files = [file
             for file in parent_dir.glob(f"*.{file_extension}")
             if file.is_file()]
    
    if not only:
        return files
    else:
        if len(files) != 1:
            raise FileExistsError(f"Make sure there is exactly one .{file_extension} file in the folder!")
        
        files = files[0]
        return files


