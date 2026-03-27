from src.misc.debug import clear_logs
from src.misc.pdf_helper import read_bold_text

from src.data.ingestion import CourseIngestor
from src.data.processing import CourseProcessor
from src.data.persistence import CourseSaver, CourseLoader
from src.misc.text_helper import remove_space
from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR

clear_logs()

# CS163 = CourseIngestor(RAW_DATA_DIR).ingest()
# CS163 = CourseProcessor(CS163).process()
# CourseSaver(CS163).save()
CS163 = CourseLoader().load()

for id, week in enumerate(CS163.weeks):
    print("i" * (id + 1))
    # for ssid, submission_set in enumerate(week.submission_set):
        # print(submission_set.submissions[0].script)

    for pid, problem in enumerate(week.problem_set.problems):
        title = problem.problem_title
        title = "".join(title.split()).lower()
        statement = problem.problem_statement

        if "-paperassignment" in title:
            print(f"{pid + 1} - 01")

def try_classify():
    W01 = CS163.weeks[1]

    from src.llm.embedding_classifier import EmbeddingClassifier

    classes = ["A local programming assignment requiring source code submission, not a handwritten response and not an external online judge task.",
            "A programming task solved through an external judging website, not merely a local course coding submission.",
            "This assignment is answered through explanation, tracing, or drawing rather than by implementing a program."]
    texts = []
    for problem in W01.problem_set.problems:
        texts.append(f"{problem.problem_title=}\n{problem.problem_statement=}")

    ecls = EmbeddingClassifier(classes)
    ecls.predict(texts)