from difflib import SequenceMatcher
from dataclasses import dataclass, field


@dataclass
class SimilarityResult:
    overall_score: float = 0
    original_line_scores: list[float] = field(default_factory=list)
    corrected_line_scores: list[float] = field(default_factory=list)


class LineSimilarityEvaluator:
    def __init__(self) -> None:
        pass

    def eval(self, original_lines: list[str], corrected_lines: list[str]) -> SimilarityResult:
        # preparing the result lists
        original_scores = [0.0] * len(original_lines)
        corrected_scores = [0.0] * len(corrected_lines)

        line_matches = SequenceMatcher(None, original_lines, corrected_lines, autojunk=False)
        overall_score = line_matches.ratio()

        for tag, i1, i2, j1, j2 in line_matches.get_opcodes():
            if tag == "equal":
                for original_line_id, corrected_line_id in zip(range(i1, i2), range(j1, j2)):
                    original_scores[original_line_id] = 1.0
                    corrected_scores[corrected_line_id] = 1.0

            if tag == "delete":
                for original_line_id in range(i1, i2):
                    original_scores[original_line_id] = 0.0
            elif tag == "insert":
                for corrected_line_id in range(j1, j2):
                    corrected_scores[corrected_line_id] = 0.0
            elif tag == "replace":
                pair_scores: list[tuple[float, int, int]] = []

                for original_line_id in range(i1, i2):
                    for corrected_line_id in range(j1, j2):
                        score = SequenceMatcher(None,
                                                original_lines[original_line_id],
                                                corrected_lines[corrected_line_id],
                                                autojunk=False
                                                ).ratio()
                        pair_scores.append((score, original_line_id, corrected_line_id))

                pair_scores.sort(key=lambda x: x[0], reverse=True)
                
                used_original = set()
                used_corrected = set()
                
                # updated lines
                for score, original_line_id, corrected_line_id in pair_scores:
                    if original_line_id in used_original:
                        continue
                    if corrected_line_id in used_corrected:
                        continue
                    
                    original_scores[original_line_id] = max(0.0, score - 0.2)
                    corrected_scores[corrected_line_id] = max(0.0, score - 0.2)
                    used_original.add(original_line_id)
                    used_corrected.add(corrected_line_id)

                # deleted lines
                for original_line_id in range(i1, i2):
                    if original_line_id in used_original:
                        continue
                    original_scores[original_line_id] = 0.0

                # added lines
                for corrected_line_id in range(j1, j2):
                    if corrected_line_id in used_corrected:
                        continue
                    corrected_scores[corrected_line_id] = 0.0
                        
        def score_fix(scores: list[float], threshold: float = 0.35):
            for id in range(len(scores)):
                if scores[id] < threshold:
                    scores[id] = 0.0
            
        score_fix(original_scores)
        score_fix(corrected_scores)
        return SimilarityResult(overall_score, original_scores, corrected_scores)
