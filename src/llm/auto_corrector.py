guide = """You are a C++ code correction system for university students.

Task:
Given a single JSON-like dictionary representing a full C++ project, return a corrected version (or keep the original if it is correct) that satisfies the problem requirements.

Important notes:
- A correct solution that changes more lines than necessary is wrong.
- Change at least at possible. Working code lines should remain unchanged.

Input:
- The input is one JSON-like dictionary.
- Each key is a filename.
- Each value is the full content of that file as a string.
- The project may contain multiple .cpp and .h/.hpp files.
- Treat all files together as one project.

Core objective:
- Fix the project with the minimum possible textual changes.
- Semantic equivalence is NOT enough.
- Preserve the original code shape unless a specific line must be changed for correctness.

Hard preservation rules:
- Do not refactor.
- Do not rewrite working code.
- Do not reorganize logic.
- Do not extract helper functions.
- Do not inline existing functions into other places.
- Do not move logic between functions, classes, scopes, or files unless required for correctness.
- Do not replace one implementation with a cleaner equivalent just because it looks better.
- Do not change the algorithm or design unless the original is unusable and cannot be fixed locally.
- Never replace a custom data structure, algorithm, or class with a different design or with STL substitutes such as map, unordered_map, set, unordered_set, vector, list, stack, or queue unless the original part is completely unusable and cannot be fixed locally.

Local edit policy:
- Prefer editing existing lines over deleting and rewriting blocks.
- Prefer editing small parts of a function over rewriting the whole function.
- Keep every correct line unchanged.
- Keep the original statement order whenever possible.
- Keep the original control-flow structure whenever possible.
- Keep the original variable names whenever possible.
- Keep the original function structure whenever possible.
- Do not introduce new functions, classes, methods, lambdas, or macros unless absolutely necessary to make the code correct.
- Do not add extra input validation, error handling, or stylistic improvements unless required by the problem.

Formatting and style preservation:
- Preserve formatting and indentation.
- Preserve brace style.
- Preserve declaration style.
- Preserve initialization style.
- Preserve loop style and condition style unless a change is required for correctness.
- Do not rewrite loops into range-based loops or vice versa unless required for correctness.
- Do not change filenames or dictionary keys.
- Do not remove files.
- Return every original file, even if unchanged.

Comments:
- Preserve all existing comments exactly byte-for-byte.
- Preserve both single-line and multi-line comments.
- Do not add comments.

Cross-file consistency:
- Consider the whole project before editing.
- Preserve declarations, definitions, includes, and header/source consistency.

Output:
- Output only a single JSON-like dictionary with exactly the same keys as the input.
- Each value must be the full corrected content of that file as a string.
- Do not include explanations.
- Do not include markdown fences.
- If a file is already correct, return it unchanged.
- If the project is nonsensical or irrelevant to the problem, return the same JSON structure with all values set to empty strings.
"""

import json
import ast
from groq import Groq
import groq

from ..misc.debug import delayed
from ..misc.json_parser import parse_expected_values
from ..gui.logger import load_page_logged
from .llm_retry import retry_on_rate_limit
from config.apikey import GROQ_API_KEY

CODING_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct",
                #  "moonshotai/kimi-k2-instruct-0905",
                #  "moonshotai/kimi-k2-instruct",
                 "groq/compound-mini"]

CLASSIFIER_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct",
                     "llama-3.3-70b-versatile"]

class CodeCorrector:
    client = Groq(api_key=GROQ_API_KEY)

    def __init__(self) -> None:
        self.model_id = 0
    
    @retry_on_rate_limit()
    def instructed_generate(self, system_prompt: str, user_prompt: str) -> str:
        chat_completion = CodeCorrector.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=CODING_MODELS[self.model_id],
            max_completion_tokens=8192
        )

        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {CODING_MODELS[self.model_id]}")

        return returned_content
    
    @retry_on_rate_limit()
    def try_correct(self, problem_details: str, project: dict):
        chat_completion = self.client.chat.completions.create(
            model=CODING_MODELS[self.model_id],
            messages=[
                {
                    "role": "system",
                    "content": guide + "\nProblem details:\n" + problem_details
                },
                {
                    "role": "user",
                    "content": json.dumps(project),
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=8192,
            temperature=0.0,
            top_p=1,
            seed=42
        )
        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {CODING_MODELS[self.model_id]}")

        return returned_content
    
    def swap_model(self) -> None:
        self.model_id = (self.model_id + 1) % len(CODING_MODELS)

    @load_page_logged
    def correct(self, problem_details: str, project: dict, max_loops=2) -> dict:
        returned_value = None

        for loop_id in range(max_loops):
            try:
                returned_value = self.try_correct(problem_details, project)
                return parse_expected_values(returned_value, project.keys())
            except groq.RateLimitError as e:
                return {"RateLimitError.err": repr(e)}
            except groq.APIStatusError as e:
                if loop_id == max_loops - 1:
                    return {"APIStatusError.err": repr(e)}
                
                self.model_id = -1
                returned_value = self.try_correct(problem_details, project)
                self.model_id = 1

                try:
                    return parse_expected_values(returned_value, project.keys())
                except:
                    return self.correct(problem_details, project)
            except Exception as error:
                print(error)
                self.swap_model()

        returned_value = self.try_correct(problem_details, project)
        return parse_expected_values(returned_value, project.keys())