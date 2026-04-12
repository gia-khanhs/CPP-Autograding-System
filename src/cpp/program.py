from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, cast
import subprocess

from clang.cindex import Index

from ..misc.debug import logged, write_log


def has_main(cpp_file: Path):
    index = Index.create()
    parsed_code = index.parse(cpp_file)

    if not parsed_code:
        return False
        
    for cursor in parsed_code.cursor.get_children():
        if cursor.kind.name == "FUNCTION_DECL" and cursor.spelling == "main":
            return True
        
    return False

@dataclass
class Script:
    file_path: Optional[Path] = None
    project_root: Optional[Path] = None
    user_includes: list[Path] = field(default_factory=list)
    __cache_file_path: Optional[Path] = None
    __cache_has_main: bool = False
    
    def __init__(self, file_path: Path | None, processing_includes: bool) -> None:
        self.file_path = file_path
        if self.file_path:
            self.project_root = self.file_path.parent
        self.user_includes = []
        self.__cache_file_path = None
        self.__cache_has_main = False
        self.index = None
        self.parsed_code = None

        if (not file_path) or (not file_path.is_file()):
            self.file_path = None
            return
        
        args = ["-x", "c++", "-std=c++17"]
        self.index = Index.create()
        self.parsed_code = self.index.parse(self.file_path, args=args)
        if not self.parsed_code:
            raise SyntaxError("The C++ file cannot be parsed!")
        
        if processing_includes:
            if self.has_main():
                self.user_includes = self.get_user_includes(file_path, file_path.parent)
        # else:
        #     folder_path = file_path.parent
        #     self.user_includes = [include_path
        #                           for include_path in folder_path.rglob("*")
        #                           if include_path.is_file() and include_path != file_path]

    def has_main(self) -> bool:
        if self.__cache_file_path == self.file_path:
            return self.__cache_has_main

        if not self.parsed_code:
            return False
        
        for cursor in self.parsed_code.cursor.get_children():
            if cursor.kind.name == "FUNCTION_DECL" and cursor.spelling == "main":
                self.__cache_file_path = self.file_path
                self.__cache_has_main = True
                return True

        self.__cache_file_path = self.file_path
        self.__cache_has_main = False
        return False

    def is_under(self, root: Path, path: Path) -> bool:
        return path.resolve().is_relative_to(root.resolve())
        
    def get_user_includes(self, main_file: Path, project_root: Path, args=None) -> list[Path]:
        if not self.parsed_code:
            return []
        
        user_includes: set[Path] = set()

        if args is None:
            args = ["-x", "c++", "-std=c++17"]

        index = Index.create()
        translation_unit = index.parse(main_file, args=args)

        for include in translation_unit.get_includes():
            if include.is_input_file: # Skip the main_file
                continue

            included = include.include
            if included is None or included.name is None:
                continue

            included_path = Path(included.name).resolve()

            if self.is_under(project_root, included_path): # not get std libs like iostream and such
                user_includes.add(included_path.relative_to(project_root))

        return list(user_includes)
    
    def prepare_includes(self) -> None:
        folder_path = Path()
        if self.file_path:
            folder_path = self.file_path.parent

        self.user_includes = [include_path
                                for include_path in folder_path.rglob("*")
                                if include_path.is_file() and include_path != self.file_path]
    
    def try_compile(self) -> bool:
        if not self.has_main():
            return False
        
        ret = subprocess.run(
            ['g++', '-fsyntax-only', str(self.file_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode

        if ret:
            return False
        
        return True
    
    def get_project_dict(self) -> dict:
        if self.file_path is None:
            return {}
        if self.project_root is None:
            self.project_root = self.file_path.parent
        
        project = {}

        with open(self.file_path, "r", encoding="utf-8") as main_file:
            main_script = main_file.read()
            project["main.cpp"] = main_script

            main_file.close()

        for include_relative_path in self.user_includes:
            with open(self.project_root / include_relative_path, "r", encoding="utf-8") as include_file:
                include_script = include_file.read()
                project[str(include_relative_path)] = include_script

                include_file.close()

        return project
    

class ScriptFromDict:
    def __init__(self, root: Path, project: dict[str, str]) -> None:
        self.root = root
        self.project = project
        self.main_file: Optional[Path] = None

    def write(self, overwrite: bool=True) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

        for relative_path, content in self.project.items():
            file_path = self.root / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_path.exists() and not overwrite:
                continue

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

    def get_cpp_files(self) -> list[Path]:
        return list(self.root.rglob("*.cpp"))

    def detect_main_file(self) -> Optional[Path]:
        preferred = self.root / "main.cpp"
        if preferred.is_file():
            self.main_file = preferred
            return preferred

        for cpp_file in self.get_cpp_files():
            if has_main(cpp_file):
                self.main_file = cpp_file
                return cpp_file

        self.main_file = None
        return None

    def load(self, processing_includes: bool=True) -> Script:
        self.write()
        main_file = self.detect_main_file()
        return Script(main_file, processing_includes=processing_includes)

    def get_project_dict(self) -> dict[str, str]:
        return dict(self.project)