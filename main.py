from pathlib import Path

from src.misc.debug import clear_logs

from src.gui.main import start_gui

clear_logs()

backend, app = start_gui()
course = backend.loaded_course

from src.data.persistence import CourseLoader
path = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\output\corrected_code")
corrected_course = CourseLoader(path).load()

from src.grading.pipeline import CourseGrader
output_path = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\output\scores")
if course is not None:
    CourseGrader(output_path).grade(course, corrected_course)