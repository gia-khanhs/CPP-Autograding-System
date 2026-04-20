from dataclasses import dataclass

from .similarity import LineSimilarityEvaluator
from .line_classifier import classify_code_lines


def src_to_lines(src: str) -> list[str]:
    lines = src.strip()
    lines = lines.splitlines()
    lines = [line for line in lines if line]
    return lines


@dataclass
class WeightedScore:
    score: float
    total_weight: float


class FileGrader:
    def __init__(self) -> None:
        self.similarity_evaluator = LineSimilarityEvaluator()
        self.line_weights = {
            "logic": 3.0,
            "input": 2.0,
            "output": 1.0,
            "other": 0.2,
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
    

class ProjectGrader:
    def __init__(self) -> None:
        self.file_grader = FileGrader()

    def _calc_weighted_score(self,
                             original_project: dict[str, str],
                             corrected_project: dict[str, str]) -> WeightedScore:
        all_filenames = set(original_project) | set(corrected_project)

        total_score = 0.0
        total_weight = 0.0

        for filename in all_filenames:
            original_src = original_project.get(filename, "")
            corrected_src = corrected_project.get(filename, "")

            original_lines = src_to_lines(original_src)
            corrected_lines = src_to_lines(corrected_src)

            file_score = self.file_grader._calc_weighted_score(original_lines, corrected_lines)
            total_score += file_score.score
            total_weight += file_score.total_weight

        return WeightedScore(total_score, total_weight)

    def grade(self,
              original_project: dict[str, str],
              corrected_project: dict[str, str]) -> float:
        if not original_project and not corrected_project:
            return 0.0

        ratio = self._calc_weighted_score(original_project, corrected_project)
        ratio = self.file_grader._safe_ratio(ratio.score, ratio.total_weight)
        final_score = 10.0 * ratio
        return final_score
