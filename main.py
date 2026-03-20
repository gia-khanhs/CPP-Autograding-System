from src.misc.logger import clear_logs
from src.misc.pdf_helper import read_bold_text

from src.data.ingestion import CourseLoader
from src.data.processing import CourseProcessor
from config.paths import RAW_DATA_DIR

clear_logs()

CS163 = CourseLoader(RAW_DATA_DIR).load()

# # weeks = CS163.weeks

# # for week in weeks:
# #     read_bold_text(week.problem_set.pdf_path)

CS163 = CourseProcessor(CS163).process()








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