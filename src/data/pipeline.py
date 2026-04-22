import json
from pathlib import Path

from .fingerprints import fingerprint_directory
from .structures import Course, Week
from .ingestion import CourseIngestor, WeekIngestor
from .processing import CourseProcessor, WeekProcessor
from .persistence import CourseLoader, CourseSaver, WeekSaver
from .consts import PS_FOLDER, SS_FOLDER, MAIN_FILE, HASH_FILE
from ..misc.debug import logged, timed
from ..misc.path import get_subfolders
from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from ..gui.logger import load_page_logged, app_log

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
    
    def get_raw_week_ids(self) -> list[int]:
        raw_weeks = get_subfolders(self.raw_dir)
        week_ids = []

        for id in range(len(raw_weeks)):
            week_name = raw_weeks[id].name
            week_name = "".join([char
                         for char in week_name
                         if char.isdigit()])
            week_ids.append(int(week_name))

        return week_ids

    @load_page_logged
    def get_outdated_week_ids(self) -> list[int]:
        outdated_weeks = []
        saved_hashes = self.get_saved_hashes()
        cur_hashes = self.calc_week_hashes()

        raw_weeks = self.get_raw_week_ids()
        processed_weeks = []

        saved_len = len(saved_hashes)
        cur_len = len(cur_hashes)
        if saved_len != cur_len:
            raise ValueError("Corrupted processed files! The number of weeks in the processed folder"
            "and the number of hashes does not match!")

        for id, week_name in enumerate(saved_hashes):
            week_id = "".join([char
                       for char in week_name
                       if char.isdigit()])
            week_id = int(week_id)
            processed_weeks.append(week_id)
            
            if saved_hashes.get(week_name) != cur_hashes.get(week_name):
                outdated_weeks.append(week_id)

        not_processed_weeks = [id
                               for id in raw_weeks
                               if id not in processed_weeks]

        return outdated_weeks + not_processed_weeks
    
    @load_page_logged
    def update_weeks(self, course: Course, outdated_week_ids: list[int]) -> Course:
        week_paths = get_subfolders(self.raw_dir)
        
        for week_id in outdated_week_ids:
            raw_week_data = WeekIngestor(week_paths[week_id - 1]).ingest()
            processed_week = WeekProcessor(raw_week_data).process()
            
            if week_id > len(course.weeks):
                course.weeks.append(processed_week)
            else:
                course.weeks[week_id - 1] = processed_week

            week_name = f"W{week_id}"
            week_path = self.processed_dir / week_name
            WeekSaver(processed_week).save(week_path)

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
        course = CourseLoader(self.processed_dir).load()
        outdated_weeks = []
        try:
            outdated_weeks = self.get_outdated_week_ids()
        except:
            app_log("load_data", "Preparing to process the whole course!")
            course = self.process_full_course()

        if len(outdated_weeks):
                course = self.update_weeks(course, outdated_weeks)

        return course
    
    # below are helper functions for the backend of the gui, added way way after the pipeline for the whole course was coded
    def process_week_if_needed(self, course: Course, week_id: int, outdated_weeks: list[int]) -> Course:
        if not week_id in outdated_weeks:
            return course

        week_paths = get_subfolders(self.raw_dir)
        raw_week_data = WeekIngestor(week_paths[week_id - 1]).ingest()
        processed_week = WeekProcessor(raw_week_data).process()
        course.weeks[week_id - 1] = processed_week

        week_name = f"W{week_id}"
        week_path = self.processed_dir / week_name
        WeekSaver(processed_week).save(week_path)

        return course
    
    def process_weeks_if_needed(self, course: Course, week_ids: list[int]) -> Course:
        outdated_weeks = self.get_outdated_week_ids()
        for week_id in week_ids:
            course = self.process_week_if_needed(course, week_id, outdated_weeks)

        return course

    @load_page_logged
    def get_with_processed_weeks(self, week_ids: list[int]) -> Course:
        try:
            course = CourseLoader(self.processed_dir).load()
            course = self.process_weeks_if_needed(course, week_ids)
        except:
            course = course = CourseIngestor(self.raw_dir).ingest()
            course = self.process_weeks_if_needed(course, week_ids)

        course = CourseLoader(self.processed_dir).load()

        old_hashes = self.get_saved_hashes()
        new_hashes = self.calc_week_hashes()
        
        for week_id in week_ids:
            week_name = 'W' + str(week_id)
            old_hashes[week_name] = new_hashes[week_name]

        with open(self.processed_dir / HASH_FILE, "w") as hash_file:
            json.dump(old_hashes, hash_file)
            hash_file.close()

        return course
    