from pathlib import Path

from src.misc.debug import clear_logs

from src.gui.main import app, get_course, get_load_page_logs
from src.cpp.line_classifier import classify_code_lines

clear_logs()

# app.run()

from src.cpp.program import Script

main_path = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\data\processed\W2\SubmissionSet\Bài của Bành_Bài của Bành\P25125085\main.cpp")
test = Script(main_path, True)
print(test.get_project_dict())

# cs163 = get_course()
# if cs163 is not None:
#     w01 = cs163.weeks[0]
#     submission_set01 = w01.submission_set[0]
#     submission01 = submission_set01.submissions[5]
#     script_path = submission01.script.file_path

#     if script_path:
#         content = None
#         with open(script_path, "r", encoding="utf-8") as main_file:
#             content = main_file.read()
#             main_file.close()

#         print(content)
#         print(classify_code_lines(content))
# print(classify_code_lines("""
# #include <bits/stdc++.h>

# using namespace std;

# int main(){
#     int n;
#     cin >> n;
#     cout << n

#     return 0;
# }
# """))