import sys
from clang.cindex import Index
from pathlib import Path
from src.cpp.program import Script

cpp_path = Path(r"D:\\102. Codeblocks\\0. main\\main.cpp")
cpp_path = Path(r"D:\\0. APCS\\2. Personal Projects\\CPP-Autograding-System\\data\\raw\\Week01\\SUBMISSIONS\\Bùi Viết Thành_805140_assignsubmission_file\\25125065_W01\\Exercise05\\Source Code.cpp")
cpp_path = Path(r"D:\\0. APCS\\2. Personal Projects\\CPP-Autograding-System\\data\\raw\\Week01\\SUBMISSIONS\\Bùi Viết Thành_805140_assignsubmission_file\\25125065_W01\\Exercise02\\Source Code.cpp")

def has_main(cpp_path: Path) -> bool:
    index = Index.create()
    parsed = index.parse(cpp_path)

    if not parsed:
        raise Exception("LOL FUNNY HAHA")
    
    for cursor in parsed.cursor.get_children():
        if cursor.kind.name == "FUNCTION_DECL" and cursor.spelling == "main":
            return True

    return False

cpp_script = Script(cpp_path)
print(cpp_script.has_main())