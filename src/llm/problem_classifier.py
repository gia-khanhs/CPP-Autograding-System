from config.apikey import GROQ_API_KEY
from .grog import CLASSIFIER_MODELS
from ..misc.debug import delayed

from groq import Groq


class ProblemClassifier:
    client = Groq(api_key=GROQ_API_KEY)

    def __init__(self) -> None:
        self.model_id = 0

    def try_classify(self, problem_details: str) -> str:
        chat_completion = self.client.chat.completions.create(
            model=CLASSIFIER_MODELS[self.model_id],
            messages=[
                {
                    "role": "system",
                    "content": """
You are classifying ONE assignment into exactly one label:

- paper
- manual_coding
- online_judge

Classify by the EXPECTED SUBMISSION TYPE, not by the topic and not by whether the text contains Input/Output sections.

Definitions

1. paper
The student is expected to do manual, handwritten, theoretical, report, or drawing work rather than submit a normal coding solution.

Strong cues for paper:
- explicitly says "Paper assignment"
- asks students to manually draw trees, graphs, tables, or structures
- asks to write a report
- asks to explain, analyze, prove, illustrate, list possible cases, or demonstrate step by step by hand
- gives diagrams/figures and asks students to work directly on them
- may mention visualization tools only for checking or testing, not for submission

2. manual_coding
The student is expected to implement code, but there is NO direct online judge link.

Strong cues for manual_coding:
- "Write a program"
- "Implement"
- "Write these functions"
- "Load from a text file"
- "Save to another text file"
- gives function signatures
- has Input/Output specifications for a program
- may include example input/output
- may ask keyboard input + file output
- no direct link to LeetCode / HackerRank / Codeforces / SPOJ / InterviewBit / similar

3. online_judge
The assignment explicitly includes a direct link to an online judge or coding platform.

Strong cues for online_judge:
- direct URL to LeetCode, HackerRank, Codeforces, SPOJ, InterviewBit, etc.
- the linked problem itself is the assignment

Decision rules (apply in this order)

Rule 1:
If there is a direct link to an online judge platform, classify as "online_judge".

Rule 2:
Otherwise, if the task is clearly manual/theory/report/drawing/step-by-step handwritten work, classify as "paper".

Rule 3:
Otherwise, if the task asks for a program or function implementation without a judge link, classify as "manual_coding".

Important anti-mistake rules

- Do NOT classify something as paper just because it has fixed input data.
- Do NOT classify something as manual_coding just because it has Input/Output sections.
- File input/output tasks are usually manual_coding unless there is a judge link.
- "Use stack", "use recursion", "use heap", etc. do not determine the label.
- A report remains paper even if it mentions coding platforms.
- Visualization/generator website links are NOT online_judge links unless they are actual judge problems.
- Wikipedia/reference links are NOT online_judge links.

Return only valid JSON:
{
  "label": "paper" | "manual_coding" | "online_judge"
}
                    """
                },
                {
                    "role": "user",
                    "content": problem_details,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1024
        )
        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {CLASSIFIER_MODELS[self.model_id]}")

        return returned_content
    
    def swap_model(self) -> None:
        n_models = len(CLASSIFIER_MODELS)
        self.model_id = (self.model_id + 1) % n_models

    @delayed
    def classify(self, problem_details: str, max_loops=5) -> str:
        returned_value = None

        for _ in range(max_loops):
            try:
                returned_value = self.try_classify(problem_details)
                return returned_value
            except Exception as error:
                print(error)
                self.swap_model()

        return '{"label": "", "confidence": 0, "reason": ""}'