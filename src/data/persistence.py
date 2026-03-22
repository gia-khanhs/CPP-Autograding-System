from pathlib import Path
from dataclasses import asdict
import json
import re
import shutil
import os

from src.data.structures import Course, Week, ProblemSet, Problem, SubmissionSet, Submission
from src.data.processing import CourseProcessor, WeekProcessor, ProblemSetProcessor, SubmissionSetProcessor
from config.paths import PROCESSED_DATA_DIR


class Saver[T]:
    def save(self, save_path: Path): ...


class SubmissionSaver(Saver[Submission]):
    def __init__(self, submission: Submission) -> None:
        self.submission = submission

    def save(self, save_path: Path) -> None:
        main_path = self.submission.script.file_path
        if main_path:
            source = main_path
            destination = save_path / "main.cpp"
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(source, destination)

            main_folder = main_path.parent
            user_includes = self.submission.script.user_includes
            for include_raw_path in user_includes:
                iterim_path = os.path.relpath(include_raw_path, main_folder)
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
        problem_folder = save_path / "ProblemSet"
        ProblemSetSaver(self.week.problem_set).save(problem_folder)

        master_submission_folder = save_path / "SubmissionSet"
        for submission_set in self.week.submission_set:
            submission_set_name = submission_set.folder_path.name
            submission_set_folder = master_submission_folder / submission_set_name
            SubmissionSetSaver(submission_set).save(submission_set_folder)


class CourseSaver(Saver[Course]):
    def __init__(self, course: Course) -> None:
        self.course = course

    def save(self, save_path: Path = PROCESSED_DATA_DIR) -> None:
        for id, week in enumerate(self.course.weeks):
            week_folder = save_path / f"W{id + 1}"
            WeekSaver(week).save(week_folder)