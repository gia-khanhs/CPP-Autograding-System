import json
from pathlib import Path

from .fingerprints import fingerprint_directory
from .structures import Course
from .ingestion import CourseIngestor, WeekIngestor
from .processing import CourseProcessor, WeekProcessor
from .persistence import CourseLoader, CourseSaver, WeekSaver
from .consts import PS_FOLDER, SS_FOLDER, MAIN_FILE, HASH_FILE
from ..misc.debug import logged, timed
from ..misc.path import get_subfolders
from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from ..gui.logger_backend import load_page_logged

class DataPipeline:
    def __init__(self, course_raw_dir: Path = RAW_DATA_DIR, course_processed_dir: Path = PROCESSED_DATA_DIR) -> None:
        self.raw_dir = course_raw_dir
        self.processed_dir = course_processed_dir

    def calc_week_hashes(self) -> dict[str, str]:
        week_hashes = {}

        week_folders = get_subfolders(self.processed_dir)

        for id, week_folder in enumerate(week_folders):
            week_name = week_folder.name
            week_hash = fingerprint_directory(week_folder)
            
            week_hashes[week_name] = week_hash

        return week_hashes
    
    def get_saved_hashes(self) -> dict[str, str]:
        saved_hashes = {}
        hash_path = self.processed_dir / HASH_FILE

        if not hash_path.is_file():
            raise FileExistsError("Cannot find saved hash file!")
        
        with open(hash_path, "r") as hash_file:
            file_content = hash_file.read()
            saved_hashes = json.loads(file_content)
            hash_file.close()

        return saved_hashes
    
    @load_page_logged
    def get_outdated_week_ids(self) -> list[int]:
        outdated_weeks = []
        saved_hashes = self.get_saved_hashes()
        cur_hashes = self.calc_week_hashes()

        saved_len = len(saved_hashes)
        cur_len = len(cur_hashes)
        if saved_len != cur_len:
            raise ValueError("Corrupted processed files! The number of weeks in the processed folder"
            "and the number of hashes does not match!")

        for id, week_name in enumerate(saved_hashes):
            if saved_hashes.get(week_name) != cur_hashes.get(week_name):
                outdated_weeks.append(id)

        return outdated_weeks
    
    @load_page_logged
    def update_weeks(self, course: Course, outdated_week_ids: list[int]) -> Course:
        new_weeks = []

        week_paths = get_subfolders(self.raw_dir)

        for week_id in outdated_week_ids:
            raw_week_data = WeekIngestor(week_paths[week_id]).ingest()
            course.weeks[week_id] = WeekProcessor(raw_week_data).process()

            week_name = f"W{week_id + 1}"
            week_path = self.processed_dir / week_name
            WeekSaver(course.weeks[week_id]).save(week_path)

        new_hashses = self.calc_week_hashes()
        with open(self.processed_dir / HASH_FILE, "w") as hash_file:
            json.dump(new_hashses, hash_file)
            hash_file.close()

        return course

    def process_full_course(self) -> Course:
        course = CourseIngestor(self.raw_dir).ingest()
        course = CourseProcessor(course).process()
        CourseSaver(course).save(self.processed_dir)

        return course

    @load_page_logged
    def get(self) -> Course:
        course = CourseLoader().load()

        try:
            outdated_weeks = self.get_outdated_week_ids()
            if len(outdated_weeks):
                course = self.update_weeks(course, outdated_weeks)
        except:
            course = self.process_full_course()

        return course