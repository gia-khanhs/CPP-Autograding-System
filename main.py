from src.misc.logger import clear_logs
clear_logs()

from src.data.ingestion import CourseLoader

course = CourseLoader().load()

