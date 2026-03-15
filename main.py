from src.misc.logger import clear_logs
from src.misc.pdf_helper import read_bold_text

from src.data.ingestion import CourseLoader
from src.data.processing import CourseProcessor
from config.paths import RAW_DATA_DIR

clear_logs()

CS163 = CourseLoader(RAW_DATA_DIR).load()

# weeks = CS163.weeks

# for week in weeks:
#     read_bold_text(week.problem_set.pdf_path)

CS163 = CourseProcessor(CS163).process()