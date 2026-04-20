from pathlib import Path

from .grade import ProjectGrader
from ..data.structures import Course, Week
from ..cpp.program import Script

import pandas as pd


class WeekGrader:
    def __init__(self, score_output_folder: Path) -> None:
        self.project_grader = ProjectGrader()

    def grade(self, processed_week: Week, corrected_week: Week):
        problems_to_grade = []

        for problem_id, problem in enumerate(processed_week.problem_set.problems):
            if problem.type != "paper":
                problems_to_grade.append(problem_id)

        for original_submission_set, corrected_submission_set in zip(processed_week.submission_set, corrected_week.submission_set):
            submitter = original_submission_set.folder_path.name
            for problem_id in problems_to_grade:
                original_src = original_submission_set.submissions[problem_id].script
                corrected_src = corrected_submission_set.submissions[problem_id].script
                score = self.project_grader.grade(original_src.get_project_dict(),
                                                  corrected_src.get_project_dict())
                
                print(f"{submitter} - {problem_id} - {score}")


class CourseGrader:
    def __init__(self, score_output_folder: Path) -> None:
        self.week_grader = WeekGrader(score_output_folder)

    def grade(self, processed_course: Course, corrected_course: Course):
        for week_id in range(len(processed_course.weeks)):
            processed_week = processed_course.weeks[week_id]
            corrected_week = None

            try:
                corrected_week = corrected_course.weeks[week_id]
            except:
                continue

            self.week_grader.grade(processed_week, corrected_week)