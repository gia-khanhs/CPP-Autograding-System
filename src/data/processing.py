from pathlib import Path
import re
from typing import Optional


from .ingestion import CourseIngestor
from .structures import Course, Week, SubmissionSet, ProblemSet, Problem

from ..misc.pdf_helper import read_bold_text, beautify_text
from ..misc.logger import logged
from ..misc.text_helper import remove_space, split_lines, join_lines


class Processor[T]:
    def process(self) -> T:
        ...


class ProblemSetProcessor(Processor[ProblemSet]):
    def __init__(self, problem_set: ProblemSet) -> None:
        self.problem_set = problem_set
    
    def get_assignment_titles(self) -> list[str]:
        assignment_titles = []

        bold_texts = read_bold_text(self.problem_set.pdf_path)

        for text in bold_texts:
            if text.startswith("Assignment"):
                assignment_titles.append(text)
            elif len(assignment_titles):
                assignment_titles[-1] += " "
                assignment_titles[-1] += text

        assignment_titles = [beautify_text(title)
                             for title in assignment_titles]
        
        return assignment_titles

    def get_problem_statements(self, problem_titles: Optional[list[str]] = None) -> list[str]:
        problem_statements = []

        if problem_titles is None:
            problem_titles = self.get_assignment_titles()
                
        titles_wo_space = remove_space(problem_titles)
        problem_set_lines = split_lines(self.problem_set.text_content)
        problem_set_lines_wo_space = remove_space(problem_set_lines)

        problem_id = 0
        start_line_id = 0
        end_line_id = 0
        for line_id, line in enumerate(problem_set_lines_wo_space):
            if line == titles_wo_space[problem_id]:
                end_line_id = line_id - 1

                if problem_id:
                    statement = problem_set_lines[start_line_id: end_line_id]
                    statement = join_lines(statement)
                    problem_statements.append(statement)

                if line == titles_wo_space[-1]: # Get the statement for the last problem
                    statement = problem_set_lines[line_id + 1:]
                    statement = join_lines(statement)
                    problem_statements.append(statement)
                    break
                
                start_line_id = line_id + 1
                problem_id += 1

        
        return problem_statements

    def process(self) -> ProblemSet:
        assignment_titles = self.get_assignment_titles()
        problem_statements = self.get_problem_statements(assignment_titles)

        for title, statement in zip(assignment_titles, problem_statements):
            problem = Problem(title, statement)
            self.problem_set.problems.append(problem)

        return self.problem_set


class SubmissionSetProcessor(Processor[list[SubmissionSet]]):
    def __init__(self, submission_set: list[SubmissionSet]) -> None:
        self.submission_set = submission_set

    def process(self) -> list[SubmissionSet]:
        return self.submission_set


class WeekProcessor(Processor[Week]):
    def __init__(self, week: Week) -> None:
        self.week = week

    def process(self) -> Week:
        self.week.problem_set = ProblemSetProcessor(self.week.problem_set).process()
        self.week.submission_set = SubmissionSetProcessor(self.week.submission_set).process()

        return self.week


class CourseProcessor(Processor[Course]):
    def __init__(self, course: Course) -> None:
        self.course = course

    def process(self) -> Course:
        for id, week in enumerate(self.course.weeks):
            processed_week = WeekProcessor(week).process()
            self.course.weeks[id] = processed_week

        return self.course

