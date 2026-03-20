import sys
from clang.cindex import Index
from pathlib import Path

cpp_path = Path(r"D:\\102. Codeblocks\\0. main\\main.cpp")
def has_main(cpp_path: Path) -> bool:
    index = Index.create()
    parsed = index.parse(cpp_path)

    if not parsed:
        raise Exception("LOL FUNNY HAHA")
    
    for cursor in parsed.cursor.get_children():
        if cursor.kind.name == "FUNCTION_DECL" and cursor.spelling == "main":
            return True

    return False

print(has_main(cpp_path))