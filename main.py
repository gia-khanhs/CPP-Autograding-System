from pathlib import Path

from src.misc.debug import clear_logs

from src.gui.main import start_gui

clear_logs()

# from src.data.pipeline import DataPipeline
# from src.data.consts import HASH_FILE
# import json
# dp = DataPipeline()
# new_hashses = dp.calc_week_hashes()
# with open(dp.processed_dir / HASH_FILE, "w") as hash_file:
#     json.dump(new_hashses, hash_file)
#     hash_file.close()

backend, app = start_gui()
course = backend.loaded_course

path = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\output\corrected_code")

from src.grading.pipeline import CourseGrader
output_path = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\output\scores")
if course is not None:
    CourseGrader(output_path).grade(course, path)