from dataclasses import dataclass

from .similarity import LineSimilarityEvaluator
from .line_classifier import classify_code_lines


def src_to_lines(src: str) -> list[str]:
    lines = src.strip()
    lines = lines.splitlines()
    lines = [line for line in lines if line]
    return lines


# @dataclass
# class FileGradeStats:
#     original_weighted_score: float
#     corrected_weighted_score: float
#     original_total_weight: float
#     corrected_total_weight: float
#     overall_score: float

@dataclass
class WeightedScore:
    score: float
    total_weight: float


class Grader:
    def __init__(self) -> None:
        self.similarity_evaluator = LineSimilarityEvaluator()
        self.line_weights = {
            "logic": 3.0,
            "input": 2.0,
            "output": 1.0,
            "other": 0.1,
        }
        self.line_score_weight = 1.0
        self.overall_score_weight = 0.0

    def _line_weight(self, label: str) -> float:
        return self.line_weights.get(label, self.line_weights["other"])

    def _total_weight(self, labels: list[str]) -> float:
        return sum(self._line_weight(label) for label in labels)

    def _weighted_sum(self, scores: list[float], labels: list[str]) -> float:
        return sum(
            score * self._line_weight(label)
            for score, label in zip(scores, labels)
        )

    def _safe_ratio(self, numerator: float, denominator: float) -> float:
        if denominator == 0.0:
            return 1.0
        return numerator / denominator

    # def _harmonic_mean(self, a: float, b: float) -> float:
    #     if a <= 0.0 or b <= 0.0:
    #         return 0.0
    #     return 2.0 * a * b / (a + b)

    # def _get_grade_stats(self, original_lines: list[str], corrected_lines: list[str]) -> FileGradeStats:
    #     similarity = self.similarity_evaluator.eval(original_lines, corrected_lines)

    #     original_labels = classify_code_lines(original_lines)
    #     corrected_labels = classify_code_lines(corrected_lines)

    #     original_weighted_score = self._weighted_sum(
    #         similarity.original_line_scores,
    #         original_labels,
    #     )
    #     corrected_weighted_score = self._weighted_sum(
    #         similarity.corrected_line_scores,
    #         corrected_labels,
    #     )

    #     original_total_weight = self._total_weight(original_labels)
    #     corrected_total_weight = self._total_weight(corrected_labels)

    #     similarity = self.similarity_evaluator.eval(original_lines, corrected_lines)

    #     return FileGradeStats(
    #         original_weighted_score,
    #         corrected_weighted_score,
    #         original_total_weight,
    #         corrected_total_weight,
    #         similarity.overall_score
    #         )

    # def _grade(self, original_src: str, corrected_src: str) -> float:
    #     original_lines = src_to_lines(original_src)
    #     corrected_lines = src_to_lines(corrected_src)

    #     if not original_lines and not corrected_lines:
    #         return 0.0

    #     grade_stats = self._get_grade_stats(original_lines, corrected_lines)
    #     original_weighted_score = grade_stats.original_weighted_score
    #     original_total_weight = grade_stats.original_total_weight
    #     corrected_weighted_score = grade_stats.corrected_weighted_score
    #     corrected_total_weight = grade_stats.corrected_total_weight
    #     overall_score = grade_stats.overall_score

    #     score_with_deletion_penalty = self._safe_ratio(original_weighted_score, original_total_weight)
    #     score_with_insertion_penalty = self._safe_ratio(corrected_weighted_score, corrected_total_weight)

    #     line_score = self._harmonic_mean(score_with_deletion_penalty, score_with_insertion_penalty)

    #     base_weight = self.line_score_weight + self.overall_score_weight
    #     if base_weight == 0.0:
    #         score = line_score
    #     else:
    #         score = (
    #             self.line_score_weight * line_score
    #             + self.overall_score_weight * overall_score
    #         ) / base_weight

    #     return max(0.0, min(1.0, score))

    def _calc_weighted_score(self, original_lines: list[str], corrected_lines: list[str]) -> WeightedScore:
        similarity = self.similarity_evaluator.eval(original_lines, corrected_lines)

        original_labels = classify_code_lines(original_lines)
        corrected_labels = classify_code_lines(corrected_lines)

        original_weighted_score = self._weighted_sum(
            similarity.original_line_scores,
            original_labels,
        )
        original_total_weight = self._total_weight(original_labels) # with deletion penalty

        insertion_penalty = self._total_weight([
            corrected_labels[line_id]
            for line_id in range(len(corrected_lines))
            if similarity.corrected_line_scores[line_id] == 0
        ])

        final_total_weight = original_total_weight + insertion_penalty # applying the insertion penalty

        return WeightedScore(original_weighted_score, final_total_weight)


    def grade(self, original_src: str, corrected_src: str) -> float:
        original_lines = src_to_lines(original_src)
        corrected_lines = src_to_lines(corrected_src)

        if not original_lines and not corrected_lines:
            return 0.0
        
        ratio = self._calc_weighted_score(original_lines, corrected_lines)
        ratio = self._safe_ratio(ratio.score, ratio.total_weight)
        final_score = 10.0 * ratio
        return final_score
