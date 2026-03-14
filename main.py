from src.misc.logger import clear_logs
clear_logs()

from src.data.ingestion import CourseLoader, WeekLoader
from config.paths import RAW_DATA_DIR

CS163 = CourseLoader(RAW_DATA_DIR).load()

for week in CS163.weeks:
    print(week.problem_set.pdf_path)