from pathlib import Path
import re
from typing import Optional
import json


from .ingestion import CourseIngestor
from .structures import Course, Week, SubmissionSet, ProblemSet, Problem

from ..llm.oj_problem import get_problem_statement
from ..misc.pdf_helper import read_bold_text, beautify_text
from ..misc.debug import logged
from ..misc.text_helper import remove_space, split_lines, join_lines, find_urls
from ..llm.problem_classifier import ProblemClassifier
from ..gui.logger import load_page_logged

class Processor[T]:
    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        if "__init__" in cls.__dict__:
            cls.__init__ = load_page_logged(cls.__init__)

    def process(self) -> T:
        ...


class ProblemSetProcessor(Processor[ProblemSet]):
    problem_classifier = ProblemClassifier()

    def __init__(self, problem_set: ProblemSet) -> None:
        self.problem_set = problem_set
    
    def get_assignment_titles(self) -> list[str]:
        assignment_titles = []

        pdf_path = self.problem_set.pdf_path if self.problem_set.pdf_path else Path()
        bold_texts = read_bold_text(pdf_path)

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
        text_content = self.problem_set.text_content if self.problem_set.text_content else ""
        problem_set_lines = split_lines(text_content)
        problem_set_lines_wo_space = remove_space(problem_set_lines)

        problem_id = 0
        start_line_id = 0
        end_line_id = 0
        for line_id, line in enumerate(problem_set_lines_wo_space):
            if line == titles_wo_space[problem_id]:
                end_line_id = line_id

                if problem_id:
                    statement = problem_set_lines[start_line_id: end_line_id]
                    statement = join_lines(statement).strip()
                    problem_statements.append(statement)

                if line == titles_wo_space[-1]: # Get the statement for the last problem
                    statement = problem_set_lines[line_id + 1:]
                    statement = join_lines(statement).strip()
                    problem_statements.append(statement)
                    break
                
                start_line_id = line_id + 1
                problem_id += 1

        
        return problem_statements

    def process(self) -> ProblemSet:
        assignment_titles = self.get_assignment_titles()
        problem_statements = self.get_problem_statements(assignment_titles) 

        for title, statement in zip(assignment_titles, problem_statements):
            problem_type = json.loads(self.problem_classifier.classify(
                f"{title=}\n{statement=}"
            ))["label"]

            if problem_type == "online_judge":
                oj_url = find_urls(statement)[0]
                statement = get_problem_statement(oj_url)

            problem = Problem(title, statement, problem_type)
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

