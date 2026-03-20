from pathlib import Path
from dataclasses import dataclass


from clang.cindex import Index


@dataclass
class Script:
    file_path: Path
    
    def __init__(self, file_path: Path) -> None:
        self.index = Index.create()
        self.parsed_code = self.index.parse(self.file_path)

        if not self.parsed_code:
            raise SyntaxError("The C++ file cannot be parsed!")

    def has_main(self) -> bool:
        for cursor in self.parsed_code.cursor.get_children():
            if cursor.kind.name == "FUNCTION_DECL" and cursor.spelling == "main":
                return True

        return False