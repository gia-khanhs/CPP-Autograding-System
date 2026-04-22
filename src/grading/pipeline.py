from pathlib import Path

from .grade import ProjectGrader
from ..data.structures import Course, Week
from ..cpp.program import Script
from ..gui.logger import app_log

import pandas as pd


from pathlib import Path
import pandas as pd

class WeekGrader:
    def __init__(self, score_output_folder: Path) -> None:
        self.project_grader = ProjectGrader()
        self.score_output_folder = score_output_folder

    def grade(self, processed_week: Week, processed_course_path: Path, corrected_course_path: Path) -> pd.DataFrame:
        problems_to_grade = []

        for problem_id, problem in enumerate(processed_week.problem_set.problems):
            # if problem.type != "paper":
            problems_to_grade.append(problem_id)

        score_table = {}

        for original_submission_set in processed_week.submission_set:
            submitter = original_submission_set.folder_path.name
            score_table[submitter] = {}

            for problem_id in problems_to_grade:
                original_src = original_submission_set.submissions[problem_id].script
                if original_src.file_path is None:
                    score_table[submitter][problem_id + 1] = None
                    continue

                rel_path = original_src.file_path.relative_to(processed_course_path)
                corrected_src = Script(corrected_course_path / rel_path, True)

                if corrected_src.file_path is None:
                    score_table[submitter][problem_id + 1] = None
                    continue

                score = self.project_grader.grade(
                    original_src.get_project_dict(),
                    corrected_src.get_project_dict()
                )

                score_table[submitter][problem_id + 1] = score
                app_log("grading", f"{submitter} - Problem {problem_id + 1}: {score}")

        score_df = pd.DataFrame.from_dict(score_table, orient="index")
        score_df.index.name = "submitter"

        score_df = score_df.reindex(columns=[problem_id + 1 for problem_id in problems_to_grade])
        score_df.columns = [f"P{col}" for col in score_df.columns]

        app_log("grading", f"Saving scores to {self.score_output_folder / processed_week.folder_path.name}_scores.xlsx")

        self.score_output_folder.mkdir(parents=True, exist_ok=True)
        output_path = self.score_output_folder / f"{processed_week.folder_path.name}_scores.xlsx"
        score_df.to_excel(output_path)

        return score_df


class CourseGrader:
    def __init__(self, score_output_folder: Path) -> None:
        self.week_grader = WeekGrader(score_output_folder)

    def grade(self, processed_course: Course, corrected_course_path: Path):
        for week_id in range(len(processed_course.weeks)):
            processed_week = processed_course.weeks[week_id]
            self.week_grader.grade(processed_week, processed_course.folder_path, corrected_course_path)