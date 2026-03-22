from src.misc.logger import clear_logs
from src.misc.pdf_helper import read_bold_text

from src.data.ingestion import CourseIngestor
from src.data.processing import CourseProcessor
from src.data.persistence import CourseSaver
from config.paths import RAW_DATA_DIR

clear_logs()

CS163 = CourseIngestor(RAW_DATA_DIR).ingest()

# # weeks = CS163.weeks

# # for week in weeks:
# #     read_bold_text(week.problem_set.pdf_path)

CS163 = CourseProcessor(CS163).process()
CourseSaver(CS163).save()
# W01 = CS163.weeks[0]
# W01_PS = W01.problem_set

# bui_viet_thanh_ss = W01.submission_set[0]
# for submission in bui_viet_thanh_ss.submissions:
#     print(submission.main_path)

W02 = CS163.weeks[1]

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