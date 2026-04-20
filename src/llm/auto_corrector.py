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
- If the project is nonsensical or irrelevant to the problem, return the same JSON structure with all values set to empty strings."""

import json
import time
import random
from functools import wraps

from google import genai
from google.genai import errors, types

from config.apikey import GEMINI_API_KEY
from ..gui.logger import load_page_logged


CODING_MODELS = [
    "gemma-4-31b-it",
    # "gemini-3.1-flash-lite-preview",
]

def retry_on_rate_limit(max_retries=6, base_delay=1.0, max_delay=60.0, retry_on=(429, 503)):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            delay = base_delay

            attempt = 0
            loop_limit = max_retries
            while attempt < loop_limit:
                try:
                    return function(*args, **kwargs)

                except errors.APIError as error:
                    if error.code not in retry_on or attempt == loop_limit:
                        raise                        

                    sleep_time = min(delay, max_delay)
                    sleep_time *= random.uniform(0.8, 1.2)

                    print(
                        f"API error {error.code}. "
                        f"Retrying in {sleep_time:.2f}s "
                        f"({attempt + 1}/{loop_limit})"
                    )

                    time.sleep(sleep_time)
                    if error.code != 503:
                        delay *= 2
                    if error.code == 503:
                        loop_limit += 1

                attempt += 1
        return wrapper
    return decorator

def _extract_json(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    thought_end = text.rfind("<channel|>")
    if thought_end != -1:
        text = text[thought_end + len("<channel|>"):].strip()

    first = text.find("{")
    last = text.rfind("}")

    if first != -1 and last != -1 and first <= last:
        return text[first:last + 1]

    return text


class GoogleAPICaller:
    client = genai.Client(api_key=GEMINI_API_KEY)

    def __init__(self, model: str = CODING_MODELS[0]) -> None:
        self.model = model

    def generate(self, user_prompt: str) -> str:
        response = GoogleAPICaller.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
        )

        returned_content = response.text

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {self.model}")

        return returned_content

    def instructed_generate(self, system_prompt: str, user_prompt: str) -> str:
        response = GoogleAPICaller.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config={
                "system_instruction": system_prompt,
                "max_output_tokens": 32768,
            },
        )

        returned_content = response.text

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {self.model}")

        return returned_content


class CodeCorrector:
    client = genai.Client(api_key=GEMINI_API_KEY)

    def __init__(self) -> None:
        self.model_id = 0

    @retry_on_rate_limit()
    def try_correct(self, problem_details: str, project: dict) -> str:
        response = self.client.models.generate_content(
            model=CODING_MODELS[self.model_id],
            contents=json.dumps(project, ensure_ascii=False, indent=2),
            config=types.GenerateContentConfig(
                system_instruction=guide + "\nProblem details:\n" + problem_details,
                response_mime_type="application/json",
                response_json_schema={
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.HIGH
                ),
                temperature=0.1,
                top_p=1,
                seed=42,
                max_output_tokens=32768,
            ),
        )

        returned_content = response.text

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {CODING_MODELS[self.model_id]}")

        return returned_content

    def swap_model(self) -> None:
        self.model_id = (self.model_id + 1) % len(CODING_MODELS)

    @load_page_logged
    def correct(self, problem_details: str, project: dict, max_loops: int = 2) -> dict:
        returned_value = None

        for _ in range(max_loops):
            try:
                returned_value = self.try_correct(problem_details, project)
                return json.loads(_extract_json(returned_value))
            except Exception as error:
                print(error)
                self.swap_model()

        returned_value = self.try_correct(problem_details, project)
        return json.loads(_extract_json(returned_value))
