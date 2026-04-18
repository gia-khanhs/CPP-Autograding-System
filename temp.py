from pathlib import Path

from src.grading.diff import LineSimilarityEvaluator

path1 = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\data\processed\W1\SubmissionSet\Bùi Viết Thành_805140_assignsubmission_file_25125065_W01\P5\main.cpp")
path2 = Path(r"D:\0. APCS\2. Personal Projects\CPP-Autograding-System\output\corrected_code\W1\SubmissionSet\Bùi Viết Thành_805140_assignsubmission_file_25125065_W01\P5\main.cpp")

with open(path1, "r", encoding="utf-8") as f:
    wrong_src = f.read()

with open(path2, "r", encoding="utf-8") as f:
    correct_src = f.read()

evaluator = LineSimilarityEvaluator()
result = evaluator.eval(wrong_src, correct_src)
print(result)