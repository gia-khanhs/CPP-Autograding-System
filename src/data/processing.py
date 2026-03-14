from pathlib import Path


from .ingestion import CourseLoader
from .structures import Course, Week, Submission, ProblemSet


class Processor[T]:
    def process(self) -> T:
        ...


class ProblemSetProcessor(Processor):
    def __init__(self, problem_set: ProblemSet) -> None:
        self.problem_set = problem_set

    def process(self) -> None:
        raise NotImplemented


class SubmissionProcessor(Processor):
    def __init__(self, submissions = list[Submission]) -> None:
        self.submissions = submissions

    def process(self) -> None:
        raise NotImplementedError


class WeekProcessor(Processor):
    def __init__(self, week: Week) -> None:
        self.week = week

    def process(self) -> None:
        raise NotImplementedError


class CourseProcessor(Processor):
    def __init__(self, course: Course) -> None:
        self.course = course

    def process(self) -> None:
        raise NotImplementedError