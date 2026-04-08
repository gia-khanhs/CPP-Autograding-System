guide = """
*You are a code correction system for university students.

Goal:
- Correct the provided C++ project so it satisfies the problem requirements.

Input format:
- The input will be a single JSON-like dictionary.
- Each key is a filename.
- Each value is the full content of that C++ source/header file as a string.
- The dictionary may contain multiple .cpp and .h files.
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
- If a file is already correct and requires no modification, output "CORRECT" for that file instead of repeating its content.
- If the entire project is already correct with no modifications needed in any file, output "CORRECT" for every file.

Output rules:
- First understand how the whole project works internally, then identify incorrect lines internally, then output the corrected project only.
- Output must be a single JSON-like dictionary with exactly the same keys as the input.
- Each output value must be either:
  - the corrected full content of that file as a string, or
  - the exact string "CORRECT" if that file needs no changes.
- Do not include explanations.
- Do not include markdown fences.
- Do not include comments unless they already exist in the original code.
- Do not reformat code.
- Do not change filenames or dictionary keys.
- If the project makes no sense at all or its logic is not relevant to the problem, return exactly:
INVALID
"""

import json
from groq import Groq

from .groq import CODING_MODELS
from ..misc.debug import delayed
from ..gui.logger_backend import load_page_logged
from config.apikey import GROQ_API_KEY

class CodeCorrector:
    client = Groq(api_key=GROQ_API_KEY)

    def __init__(self) -> None:
        self.model_id = 0
    
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
    
    def try_correct(self, project: dict):
        chat_completion = self.client.chat.completions.create(
            model=CODING_MODELS[self.model_id],
            messages=[
                {
                    "role": "system",
                    "content": guide
                },
                {
                    "role": "user",
                    "content": project,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=8192
        )
        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {CODING_MODELS[self.model_id]}")

        return returned_content

    def swap_model(self) -> None:
        self.model_id = (self.model_id + 1) % len(CODING_MODELS)

    @delayed
    @load_page_logged
    def classify(self, project: dict, max_loops=5) -> dict:
        returned_value = None

        for _ in range(max_loops):
            try:
                returned_value = self.try_correct(project)
                return json.loads(returned_value)
            except Exception as error:
                print(error)
                self.swap_model()

        returned_value = self.try_correct(project)
        return json.loads(returned_value)