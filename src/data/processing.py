from pathlib import Path


from .ingestion import CourseLoader
from .structures import Course, Week, Submission, ProblemSet, Problem

from ..misc.pdf_helper import read_bold_text
from ..misc.logger import logged


class Processor[T]:
    def process(self) -> T:
        ...


class ProblemSetProcessor(Processor[ProblemSet]):
    def __init__(self, problem_set: ProblemSet) -> None:
        self.problem_set = problem_set

    @logged
    def get_assignment_titles(self) -> list[str]:
        assignment_titles = []

        bold_texts = read_bold_text(self.problem_set.pdf_path)
        bold_texts = [text.strip()
                      for text in bold_texts]

        for text in bold_texts:
            if text.startswith("Assignment"):
                assignment_titles.append(text)
            elif len(assignment_titles):
                assignment_titles[-1].append(" ")
                assignment_titles[-1].append(text)

        return assignment_titles

    def process(self) -> ProblemSet:
        assignment_titles = self.get_assignment_titles()

        for title in assignment_titles:
            problem = Problem(title, "")
            self.problem_set.problems.append(problem)

        return self.problem_set


class SubmissionProcessor(Processor[list[Submission]]):
    def __init__(self, submissions: list[Submission]) -> None:
        self.submissions = submissions

    def process(self) -> list[Submission]:
        return []


class WeekProcessor(Processor[Week]):
    def __init__(self, week: Week) -> None:
        self.week = week

    def process(self) -> Week:
        self.week.problem_set = ProblemSetProcessor(self.week.problem_set).process()
        self.week.submissions = SubmissionProcessor(self.week.submissions).process()

        return self.week


class CourseProcessor(Processor[Course]):
    def __init__(self, course: Course) -> None:
        self.course = course

    def process(self) -> Course:
        for id, week in enumerate(self.course.weeks):
            processed_week = WeekProcessor(week).process()
            self.course.weeks[id] = processed_week

        return self.course

