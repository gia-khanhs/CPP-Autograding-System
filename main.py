from src.misc.logger import clear_logs
clear_logs()

from src.data.ingestion import CourseLoader, WeekLoader
from config.paths import RAW_DATA_DIR

w01 = WeekLoader(RAW_DATA_DIR / "Week01").load()