from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from .logger import app_log
from .state import AppState, BatchRunResult, FailureItem, ProgressUpdate, RunConfig, WeekResult
from ..data.pipeline import DataPipeline
from ..data.structures import Course, Week
from ..grading.correction import CourseCorrector, WeekCorrector
from ..grading.pipeline import CourseGrader, WeekGrader


ProgressCallback = Callable[[ProgressUpdate], None]


class AppBackend:
    def __init__(self) -> None:
        self.state = AppState()
        self.code_corrector: Optional[CourseCorrector] = None
        self.course_grader: Optional[CourseGrader] = None

    def get_available_week_names(self, raw_dir: Path) -> list[str]:
        if not raw_dir.is_dir():
            return []

        week_names = [folder.name for folder in raw_dir.iterdir() if folder.is_dir()]
        week_names.sort()
        return week_names

    def load_data(self, raw_dir: Path, processed_dir: Path) -> Course:
        self.state.raw_dir = raw_dir
        self.state.processed_dir = processed_dir
        self.state.loaded_course = DataPipeline(raw_dir, processed_dir).get()
        return self.state.loaded_course

    def correct_code(self, corrected_dir: Path) -> None:
        self.state.corrected_dir = corrected_dir
        if self.state.loaded_course is None:
            app_log("autocorrection", "No course data loaded yet.")
            return

        self.code_corrector = CourseCorrector(
            self.state.loaded_course,
            self.state.processed_dir,
            self.state.corrected_dir,
        )
        self.code_corrector.correct()

    def grade(self, grade_dir: Path) -> None:
        self.state.grade_dir = grade_dir
        if self.state.loaded_course is None:
            app_log("grading", "No course data loaded yet.")
            return

        self.course_grader = CourseGrader(grade_dir)
        self.course_grader.grade(self.state.loaded_course, self.state.corrected_dir)

    def get_runnable_week_names(self, raw_dir: Path, processed_dir: Path) -> list[str]:
        if self.state.loaded_course is not None:
            return [week.folder_path.name
                    for week in self.state.loaded_course.weeks
                    if week is not None]

        try:
            course = DataPipeline(raw_dir, processed_dir).get()
            return [week.folder_path.name
                    for week in course.weeks
                    if week is not None]
        except Exception:
            return self.get_available_week_names(raw_dir)

    def run_grading_batch(
        self,
        config: RunConfig,
        on_progress: Optional[ProgressCallback] = None,
    ) -> BatchRunResult:
        self.state.raw_dir = config.raw_dir
        self.state.processed_dir = config.processed_dir
        self.state.corrected_dir = config.corrected_dir
        self.state.grade_dir = config.grade_dir

        self._emit_progress(
            on_progress,
            ProgressUpdate(stage="loading", message="Loading/Processing course data"),
        )

        selected_week_ids = []
        for _, week_name in config.selected_week_names:
            week_id = int("".join([char
                               for char in week_name
                               if char.isdigit()]))
            selected_week_ids.append(week_id)

        course = DataPipeline(config.raw_dir, config.processed_dir).get_with_processed_weeks(selected_week_ids)
        self.state.loaded_course = course

        selected_weeks = self._select_weeks(course, config.selected_week_names)
        total_weeks = len(selected_weeks)

        failures: list[FailureItem] = []
        week_results: list[WeekResult] = []

        if total_weeks == 0:
            app_log("grading", "No weeks selected.")
            result = BatchRunResult(config=config, week_results=[], failures=[])
            self.state.last_run_result = result
            self._emit_progress(
                on_progress,
                ProgressUpdate(
                    stage="done",
                    message="Nothing to run",
                    completed_weeks=0,
                    total_weeks=0,
                    failures=0,
                ),
            )
            return result

        for week_index, week in enumerate(selected_weeks, start=1):
            if week is None:
                continue
            week_name = week.folder_path.name
            self._emit_progress(
                on_progress,
                ProgressUpdate(
                    stage="week_start",
                    message=f"Preparing {week_name}",
                    week_name=week_name,
                    completed_weeks=week_index - 1,
                    total_weeks=total_weeks,
                    failures=len(failures),
                ),
            )

            if config.run_autocorrection:
                self._emit_progress(
                    on_progress,
                    ProgressUpdate(
                        stage="correcting",
                        message=f"Autocorrecting {week_name}",
                        week_name=week_name,
                        completed_weeks=week_index - 1,
                        total_weeks=total_weeks,
                        failures=len(failures),
                    ),
                )
                try:
                    week_corrector = WeekCorrector(
                        week,
                        config.processed_dir,
                        config.corrected_dir,
                    )
                    week_corrector.correct()
                except Exception as exc:
                    failure = FailureItem(
                        week_name=week_name,
                        submitter="",
                        problem_label="",
                        stage="autocorrection",
                        reason=str(exc),
                        path=str(config.corrected_dir / week_name),
                    )
                    failures.append(failure)
                    app_log("autocorrection", f"{week_name}: {exc}")

            self._emit_progress(
                on_progress,
                ProgressUpdate(
                    stage="grading",
                    message=f"Grading {week_name}",
                    week_name=week_name,
                    completed_weeks=week_index - 1,
                    total_weeks=total_weeks,
                    failures=len(failures),
                ),
            )

            try:
                week_result = self._grade_single_week(week, course.folder_path, config.corrected_dir, config.grade_dir)
                week_results.append(week_result)
                failures.extend(week_result.failures)
            except Exception as exc:
                failure = FailureItem(
                    week_name=week_name,
                    submitter="",
                    problem_label="",
                    stage="grading",
                    reason=str(exc),
                    path=str(config.grade_dir / f"{week_name}_scores.xlsx"),
                )
                failures.append(failure)
                app_log("grading", f"{week_name}: {exc}")

            self._emit_progress(
                on_progress,
                ProgressUpdate(
                    stage="week_done",
                    message=f"Finished {week_name}",
                    week_name=week_name,
                    completed_weeks=week_index,
                    total_weeks=total_weeks,
                    failures=len(failures),
                ),
            )

        result = BatchRunResult(config=config, week_results=week_results, failures=failures)
        self.state.last_run_result = result

        self._emit_progress(
            on_progress,
            ProgressUpdate(
                stage="done",
                message="Run completed",
                completed_weeks=total_weeks,
                total_weeks=total_weeks,
                failures=len(failures),
            ),
        )

        return result

    def _grade_single_week(
        self,
        week: Week,
        processed_course_path: Path,
        corrected_course_path: Path,
        grade_dir: Path,
    ) -> WeekResult:
        week_grader = WeekGrader(grade_dir)
        score_df = week_grader.grade(week, processed_course_path, corrected_course_path)
        output_path = grade_dir / f"{week.folder_path.name}_scores.xlsx"

        failures: list[FailureItem] = []
        # for submitter, row in score_df.iterrows():
        #     for problem_label, score in row.items():
        #         if pd.isna(score):
        #             failures.append(
        #                 FailureItem(
        #                     week_name=week.folder_path.name,
        #                     submitter=str(submitter),
        #                     problem_label=str(problem_label),
        #                     stage="grading",
        #                     reason="Missing original or corrected submission",
        #                     path=str(output_path),
        #                 )
        #             )

        return WeekResult(
            week_name=week.folder_path.name,
            score_df=score_df,
            output_path=output_path,
            failures=failures,
        )

    def _select_weeks(self, course: Course, selected_week_names: list[str]) -> list[Optional[Week]]:
        if not selected_week_names:
            return list(course.weeks)

        selected_name_set = set(selected_week_names)
        return [week
                for week in course.weeks
                if week is not None and week.folder_path.name in selected_name_set]

    def _emit_progress(
        self,
        on_progress: Optional[ProgressCallback],
        update: ProgressUpdate,
    ) -> None:
        if on_progress is None:
            return

        on_progress(update)
