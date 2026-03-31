from pathlib import Path

from src.misc.debug import clear_logs

from src.data.pipeline import DataPipeline

clear_logs()

data_pipeline = DataPipeline()
CS163 = data_pipeline.get()

# CS163 = CourseIngestor(RAW_DATA_DIR).ingest()
# CS163 = CourseProcessor(CS163).process()
# CourseSaver(CS163).save()

# CS163 = CourseLoader().load()

# classifier = ProblemClassifier()

# for id, week in enumerate(CS163.weeks):
#     print("i" * (id + 1))
#     # for ssid, submission_set in enumerate(week.submission_set):
#         # print(submission_set.submissions[0].script)

#     for pid, problem in enumerate(week.problem_set.problems):
#         title = problem.problem_title
#         title = "".join(title.split()).lower()
#         statement = problem.problem_statement

#         print(classifier.classify(f"{title=}\n{statement=}"))

# from src.misc.oj_problem import get_problem_statement
# print(get_problem_statement("https://www.hackerrank.com/challenges/ctci-ice-cream-parlor/problem"))