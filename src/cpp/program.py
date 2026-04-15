from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, cast
import subprocess

from clang.cindex import Index

from ..misc.debug import logged, write_log


SOURCE_EXTS = {".cpp", ".cc", ".cxx"}
HEADER_EXTS = {".h", ".hh", ".hpp", ".hxx", ".inl", ".ipp"}
CPP_PROJECT_EXTS = SOURCE_EXTS | HEADER_EXTS

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
        self.file_path: Optional[Path] = file_path.resolve() if file_path else None
        self.project_root: Optional[Path] = self.file_path.parent if self.file_path else None
        self.user_includes: list[Path] = []
        self.__cache_file_path: Optional[Path] = None
        self.__cache_has_main: bool = False
        self.index = None
        self.parsed_code = None

        if self.file_path is None or not self.file_path.is_file():
            self.file_path = None
            self.project_root = None
            return

        args = ["-x", "c++", "-std=c++17"]

        self.index = Index.create()
        self.parsed_code = self.index.parse(str(self.file_path), args=args)
        if self.parsed_code is None:
            raise SyntaxError("The C++ file cannot be parsed!")

        if processing_includes:
            self.prepare_includes()

    def has_main(self) -> bool:
        if self.__cache_file_path == self.file_path:
            return self.__cache_has_main

        if self.parsed_code is None:
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
        if args is None:
            args = ["-x", "c++", "-std=c++17"]

        index = Index.create()
        translation_unit = index.parse(str(main_file), args=args)
        if translation_unit is None:
            return []

        project_root = project_root.resolve()
        included_files: set[Path] = set()

        for include in translation_unit.get_includes():
            if include.is_input_file:
                continue

            included = include.include
            if included is None or included.name is None:
                continue

            included_path = Path(included.name).resolve()

            if self.is_under(project_root, included_path):
                rel_path = included_path.relative_to(project_root)
                if rel_path.suffix.lower() in CPP_PROJECT_EXTS:
                    included_files.add(rel_path)

        return sorted(included_files)

    def discover_project_files(self) -> list[Path]:
        if self.file_path is None or self.project_root is None:
            return []

        project_files: list[Path] = []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if path.resolve() == self.file_path.resolve():
                continue
            if path.suffix.lower() not in CPP_PROJECT_EXTS:
                continue

            project_files.append(path.resolve().relative_to(self.project_root))

        return sorted(project_files)

    def prepare_includes(self) -> None:
        self.user_includes = self.discover_project_files()

    def try_compile(self) -> bool:
        if self.file_path is None or self.project_root is None:
            return False
        if not self.has_main():
            return False

        source_files = [self.file_path]

        for rel_path in self.user_includes:
            abs_path = self.project_root / rel_path
            if abs_path.suffix.lower() in SOURCE_EXTS:
                source_files.append(abs_path)

        seen = set()
        unique_sources = []
        for path in source_files:
            key = path.resolve()
            if key not in seen:
                seen.add(key)
                unique_sources.append(path)

        ret = subprocess.run(
            [
                "g++",
                "-std=c++17",
                "-fsyntax-only",
                "-I",
                str(self.project_root),
                *map(str, unique_sources),
            ],
            cwd=self.project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode

        return ret == 0

    def get_project_dict(self) -> dict[str, str]:
        if self.file_path is None:
            return {}

        if self.project_root is None:
            self.project_root = self.file_path.parent

        project: dict[str, str] = {}

        with open(self.file_path, "r", encoding="utf-8") as main_file:
            project["main.cpp"] = main_file.read()

        for rel_path in self.user_includes:
            abs_path = self.project_root / rel_path

            if not abs_path.is_file():
                continue

            with open(abs_path, "r", encoding="utf-8") as include_file:
                project[str(rel_path)] = include_file.read()

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
                f.close()

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