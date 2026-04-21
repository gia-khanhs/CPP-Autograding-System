guide = """*You are a code correction system for university students.
Goal:
- Correct the provided C++ project so it satisfies the problem requirements.

Input format:
- The input will be a single JSON-like dictionary.
- Each key is a filename.
- Each value is the full content of that C++ source/header file as a string.
- The dictionary may contain multiple .cpp and .h/.hpp files.
- Treat all files together as one project.

Rules:
- Apply the minimum necessary changes.
- Preserve the original structure, formatting, file organization, and logic whenever possible.
- Do not refactor, optimize, or redesign working parts.
- Keep all working lines unchanged.
- Only modify lines required to make the solution correct.
- Do not remove files.
- Preserve all original keys from the input.
- Return every original file.
- Consider cross-file dependencies such as declarations, definitions, includes, and header/source consistency.
- If a file is already correct and requires no modification, return it unchanged.

Output rules:
- First understand how the whole project works internally, then identify incorrect lines internally, then output the corrected project only.
- Output must be a single JSON-like dictionary with exactly the same keys as the input.
- Each output value must be the corrected full content of that file as a string.
- Do not include explanations.
- Do not include markdown fences.
- Do not include comments unless they already exist in the original code.
- Do not reformat code.
- Do not change filenames or dictionary keys.
- If the project makes no sense at all or its logic is not relevant to the problem, return the JSON with the keys unchanged, and values being empty"""

import json
import time
import random
from functools import wraps

from google import genai
from google.genai import errors, types

from config.apikey import GEMINI_API_KEY
from ..gui.logger import autocorrection_page_logged, app_log


CODING_MODELS = [
    # "gemma-4-26b-a4b-it",
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
    

    def __init__(self, model: str = CODING_MODELS[0]) -> None:
        self.model = model
        self.client = client = genai.Client(api_key=GEMINI_API_KEY)

    def generate(self, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
        )

        returned_content = response.text

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {self.model}")

        return returned_content

    def instructed_generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
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
    def __init__(self) -> None:
        self.model_id = 0
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    @retry_on_rate_limit()
    def try_correct(self, problem_details: str, project: dict) -> str:
        app_log("autocorrection", f"Sending request with {CODING_MODELS[self.model_id]}...")
        start = time.perf_counter()

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
                # thinking_config=types.ThinkingConfig(
                #     thinking_level=types.ThinkingLevel.LOW,
                #     include_thoughts=False,
                # ),
                temperature=0.1,
                top_p=1,
                seed=42,
                max_output_tokens=32768,
            ),
        )

        app_log("autocorrection", f"Response received in {time.perf_counter() - start:.2f}s")
        returned_content = response.text

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {CODING_MODELS[self.model_id]}")

        return returned_content

    def swap_model(self) -> None:
        self.model_id = (self.model_id + 1) % len(CODING_MODELS)

    @autocorrection_page_logged
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
