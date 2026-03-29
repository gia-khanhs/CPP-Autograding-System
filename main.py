from pathlib import Path

from src.misc.debug import clear_logs
from src.misc.pdf_helper import read_bold_text

from src.data.ingestion import CourseIngestor, WeekIngestor
from src.data.processing import CourseProcessor, WeekProcessor
from src.data.persistence import CourseSaver, CourseLoader
from src.misc.text_helper import remove_space
from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

from src.llm.problem_classifier import ProblemClassifier

clear_logs()


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
