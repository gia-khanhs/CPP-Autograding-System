from pathlib import Path

from .grade import ProjectGrader
from ..data.structures import Course, Week
from ..cpp.program import Script

import pandas as pd


class WeekGrader:
    def __init__(self, score_output_folder: Path) -> None:
        self.project_grader = ProjectGrader()

    def grade(self, processed_week: Week, processed_course_path: Path, corrected_course_path: Path):
        problems_to_grade = []
        processed_folder = processed_week.folder_path

        for problem_id, problem in enumerate(processed_week.problem_set.problems):
            # if problem.type != "paper":
                problems_to_grade.append(problem_id)

        for original_submission_set in processed_week.submission_set:
            submitter = original_submission_set.folder_path.name
            for problem_id in problems_to_grade:
                original_src = original_submission_set.submissions[problem_id].script
                if original_src.file_path is None:
                    continue

                rel_path = original_src.file_path.relative_to(processed_course_path)
                corrected_src = Script(corrected_course_path / rel_path, True)


                score = self.project_grader.grade(original_src.get_project_dict(),
                                                corrected_src.get_project_dict())
                
                print(f"{submitter} - {problem_id + 1} - {score}")


class CourseGrader:
    def __init__(self, score_output_folder: Path) -> None:
        self.week_grader = WeekGrader(score_output_folder)

    def grade(self, processed_course: Course, corrected_course_path: Path):
        for week_id in range(len(processed_course.weeks)):
            processed_week = processed_course.weeks[week_id]
            self.week_grader.grade(processed_week, processed_course.folder_path, corrected_course_path)