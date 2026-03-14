import subprocess
from pathlib import Path

class Compiler:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.compiled_exe: Path | None = None


    def compile(self) -> int:
        exe_path = self.file_path.with_suffix('.exe')
        
        ret = subprocess.run(
            ['g++', str(self.file_path), '-o', str(exe_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode

        if ret == 0: self.compiled_exe = exe_path

        return ret
    

    def is_compiled(self) -> bool:
        if self.compiled_exe == None: return False
        
        return True
    
class CodeSubmission:
    def __init__(self, directory: Path, compiler = Compiler) -> None:
        self.directory = directory
        self.raw_source_directory = directory / 'main.cpp'
        self.raw_program = compiler(self.raw_source_directory)