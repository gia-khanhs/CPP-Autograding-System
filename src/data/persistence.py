from pathlib import Path
from dataclasses import asdict
import json
import re
import shutil
import os

from .structures import Course, Week, ProblemSet, Problem, SubmissionSet, Submission
from .structures import LazyProblem, LazySubmission
from .processing import CourseProcessor, WeekProcessor, ProblemSetProcessor, SubmissionSetProcessor
from .fingerprints import fingerprint_directory
from .consts import PS_FOLDER, SS_FOLDER, MAIN_FILE, HASH_FILE
from ..misc.path import get_subfolders, get_files_of_type
from ..misc.debug import timed, logged
from ..cpp.program import Script
from ..gui.logger import load_page_logged
from config.paths import PROCESSED_DATA_DIR



#region saver
class Saver[T]:
    # def __init_subclass__(cls, **kwargs) -> None:
    #     super().__init_subclass__(**kwargs)

    #     if "__init__" in cls.__dict__:
    #         cls.__init__ = load_page_logged(cls.__init__)

    def save(self, save_path: Path): ...


class SubmissionSaver(Saver[Submission]):
    def __init__(self, submission: Submission) -> None:
        self.submission = submission

    def save(self, save_path: Path) -> None:
        main_path = self.submission.script.file_path
        if main_path:
            source = main_path
            destination = save_path / MAIN_FILE
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, destination)

            main_folder = main_path.parent
            user_includes = self.submission.script.user_includes
            for iterim_path in user_includes:
                # iterim_path = os.path.relpath(include_raw_path, main_folder)
                include_raw_path = main_folder / iterim_path
                include_processed_path = save_path / iterim_path
                include_processed_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(include_raw_path, include_processed_path)

class SubmissionSetSaver(Saver[SubmissionSet]):
    def __init__(self, submission_set: SubmissionSet) -> None:
        self.submission_set = submission_set

    def save(self, save_path: Path) -> None:
        for submission in self.submission_set.submissions:
            submission_name = submission.folder_path.name
            submission_name = re.sub(r'[a-zA-Z]', '', submission_name)
            submission_name = submission_name.strip()
            submission_name = submission_name.lstrip("0")
            submission_name = "P" + submission_name

            submission_folder = save_path / submission_name
            SubmissionSaver(submission).save(submission_folder)



class ProblemSaver(Saver[Problem]):
    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    def save(self, save_path: Path) -> None:
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as save_file:
            json.dump(asdict(self.problem), save_file)
            save_file.close()


class ProblemSetSaver(Saver[ProblemSet]):
    def __init__(self, problem_set: ProblemSet) -> None:
        self.problem_set = problem_set

    def save(self, save_path: Path) -> None:
        for id, problem in enumerate(self.problem_set.problems):
            problem_file = save_path / f"P{id + 1}.json"
            ProblemSaver(problem).save(problem_file)


class WeekSaver(Saver[Week]):
    def __init__(self, week: Week) -> None:
        self.week = week

    def save(self, save_path: Path) -> None:
        problem_folder = save_path / PS_FOLDER
        problem_folder.mkdir(parents=True, exist_ok=True)
        ProblemSetSaver(self.week.problem_set).save(problem_folder)

        master_submission_folder = save_path / SS_FOLDER
        master_submission_folder.mkdir(parents=True, exist_ok=True)
        for submission_set in self.week.submission_set:
            archive_folder_name = submission_set.archive_folder.name if submission_set.archive_folder else ""
            submission_set_name = f"{archive_folder_name}_{submission_set.folder_path.name}"
            submission_set_folder = master_submission_folder / submission_set_name
            SubmissionSetSaver(submission_set).save(submission_set_folder)


class CourseSaver(Saver[Course]):
    def __init__(self, course: Course) -> None:
        self.course = course

    def save(self, save_path: Path = PROCESSED_DATA_DIR) -> None:
        week_hashes = {}
        for id, week in enumerate(self.course.weeks):
            week_name = f"W{id + 1}"
            week_folder = save_path / week_name
            WeekSaver(week).save(week_folder)

            week_hash = fingerprint_directory(week_folder)
            week_hashes[week_name] = week_hash

        with open(save_path / HASH_FILE, "w") as hash_file:
            json.dump(week_hashes, hash_file)
            hash_file.close()
#endregion

#region loader
class Loader[T]:
    def __init__(self, load_path: Path) -> None:
        self.load_path = load_path

    # def __init_subclass__(cls, **kwargs) -> None:
    #     super().__init_subclass__(**kwargs)

    #     if "__init__" in cls.__dict__:
    #         cls.__init__ = load_page_logged(cls.__init__)
    
    def load(self, *args, **kargs) -> T: ...


class SubmissionLoader(Loader[LazySubmission]):
    def __init__(self, load_path: Path) -> None:
        super().__init__(load_path)

    # def load(self) -> Submission | None:
    #     main_file = self.load_path / MAIN_FILE

    #     if not main_file.is_file():
    #         return None
    #     else:
    #         return Submission(self.load_path, Script(main_file, False))

    def load(self) -> LazySubmission:
        self.main_file = self.load_path / MAIN_FILE
        return LazySubmission(self.main_file)


class SubmissionSetLoader(Loader[SubmissionSet]):
    def __init__(self, load_path: Path) -> None:
        super().__init__(load_path)

    def load(self, n_problems: int) -> SubmissionSet:
        if n_problems == 0:
            n_problems = 99

        submissions = []
        for id in range(n_problems):
            submission_problem_folder = self.load_path / f"P{id + 1}"
            submission = SubmissionLoader(submission_problem_folder).load()

            submissions.append(submission)

        submission_set = SubmissionSet(self.load_path, None, submissions)
        return submission_set


class ProblemLoader(Loader[LazyProblem]):
    def __init__(self, load_path: Path) -> None:
        super().__init__(load_path)

    # def load(self) -> Problem:
    #     problem_dict = None

    #     with open(self.load_path, "r", encoding="utf-8") as saved_file:
    #         saved_problem = saved_file.read()
    #         problem_dict =  json.loads(saved_problem)

    #         saved_file.close()

    #     return Problem(**problem_dict)

    def load(self) -> LazyProblem:
        return LazyProblem(self.load_path)


class ProblemSetLoader(Loader[ProblemSet]):
    def __init__(self, load_path: Path) -> None:
        super().__init__(load_path)

    def load(self) -> ProblemSet:
        problems = []
        problem_paths = get_files_of_type(self.load_path, "json", False)
        for problem_path in problem_paths:
            problem = ProblemLoader(problem_path).load()
            problems.append(problem)

        return ProblemSet(None, None, problems)


class WeekLoader(Loader[Week]):
    def __init__(self, load_path: Path) -> None:
        super().__init__(load_path)

    def load(self) -> Week:
        problem_set_path = self.load_path / PS_FOLDER
        submission_set_paths = get_subfolders(self.load_path / SS_FOLDER)

        problem_set = ProblemSetLoader(problem_set_path).load()
        n_problems = len(problem_set.problems)
        
        submission_sets = []
        for submission_set_path in submission_set_paths:
            submission_set = SubmissionSetLoader(submission_set_path).load(n_problems)
            submission_sets.append(submission_set)

        return Week(self.load_path, problem_set, submission_sets)


class CourseLoader(Loader[Course]):
    def __init__(self, load_path: Path = PROCESSED_DATA_DIR) -> None:
        super().__init__(load_path)

    def load(self) -> Course:
        week_paths = get_subfolders(self.load_path)
        weeks = []
        for week_path in week_paths:
            week = WeekLoader(week_path).load()
            weeks.append(week)

        return Course(self.load_path, weeks)
#endregion