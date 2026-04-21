from pathlib import Path

from ..llm.auto_corrector import CodeCorrector
from ..cpp.program import Script, ScriptFromDict
from ..data.structures import Course, Problem, Week
from ..data.persistence import CourseLoader
from ..gui.logger import app_log, autocorrection_page_logged

from config.paths import PROCESSED_DATA_DIR, CORRECTED_CODE_DIR

class ScriptCorrector:
    code_corrector = CodeCorrector()

    def __init__(self, problem_details, processed_folder: Path = PROCESSED_DATA_DIR, corrected_folder: Path = CORRECTED_CODE_DIR) -> None:
        self.processed_folder = processed_folder
        self.corrected_folder = corrected_folder
        self.problem_details = problem_details

    def correct(self, script: Script, no_recorrect: bool = True) -> Script:
        if script.file_path is None:
            return script
        
        rel_script_path = script.file_path.relative_to(self.processed_folder)
        new_script_path = self.corrected_folder / rel_script_path
        script_root = new_script_path.parent

        if new_script_path.is_file():
            app_log("autocorrection", f"{script.file_path} has already been corrected!")
            return Script(new_script_path, True)

        app_log("autocorrection", f"Correcting {script.file_path}!")

        script_dict = script.get_project_dict()
        corrected_dict = self.code_corrector.correct(self.problem_details, script_dict)
        corrected_script = ScriptFromDict(script_root, corrected_dict).load()

        return corrected_script
    
class BulkScriptCorrector:
    def __init__(self, problem: Problem, proccessed_folder: Path = PROCESSED_DATA_DIR, corrected_folder: Path = CORRECTED_CODE_DIR) -> None:
        self.problem = problem
        problem_details = f"{problem.problem_title=}\n{problem.problem_statement=}"
        self.script_corrector = ScriptCorrector(problem_details, proccessed_folder, corrected_folder)

    def correct(self, scripts: list[Script]) -> list[Script]:
        corrected_scripts = []
        for script in scripts:
            corrected_script = self.script_corrector.correct(script)
            corrected_scripts.append(corrected_script)

        return corrected_scripts
    
class WeekCorrector:
    def __init__(self, week: Week, processed_folder: Path = PROCESSED_DATA_DIR, corrected_folder: Path = CORRECTED_CODE_DIR) -> None:
        self.processed_folder = processed_folder
        self.corrected_folder = corrected_folder
        
        self.week = week
        self.problem_correctors: list[BulkScriptCorrector] = []
        self.scripts_by_problem: list[list[Script]] = []

        self.init_problem_correctors()
        self.init_scripts_by_problem()

    def init_problem_correctors(self) -> None:
        for problem in self.week.problem_set.problems:
            corrector = BulkScriptCorrector(problem, self.processed_folder, self.corrected_folder)
            self.problem_correctors.append(corrector)

    def init_scripts_by_problem(self) -> None:
        for problem_id in range(len(self.problem_correctors)):
            problem = self.week.problem_set.problems[problem_id]
            # if problem.type == "paper":
            #     self.scripts_by_problem.append([])
            #     continue

            scripts = []
            for submission_set in self.week.submission_set:
                script = submission_set.submissions[problem_id].script
                scripts.append(script)

            self.scripts_by_problem.append(scripts)

    def correct(self) -> list[list[Script]]:
        corrected_week = []

        for problem_corrector, problem_submissions in zip(self.problem_correctors, self.scripts_by_problem):
            corrected_problem_scripts = problem_corrector.correct(problem_submissions)
            corrected_week.append(corrected_problem_scripts)

        return corrected_week
    
class CourseCorrector:
    @autocorrection_page_logged
    def __init__(self, course: Course, processed_folder: Path = PROCESSED_DATA_DIR, corrected_folder: Path = CORRECTED_CODE_DIR) -> None:
        self.course = course
        self.week_correctors = []

        for week_id, week in enumerate(course.weeks):
            self.week_correctors.append(WeekCorrector(week, processed_folder, corrected_folder))
    
    @autocorrection_page_logged
    def correct(self) -> Course:
        for week_corrector in self.week_correctors:
            week_corrector.correct()

        course = CourseLoader(CORRECTED_CODE_DIR).load()
        return course
        