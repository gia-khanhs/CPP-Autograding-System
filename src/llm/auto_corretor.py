guide = """
*You are a code correction system for university students.

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
- If the project makes no sense at all or its logic is not relevant to the problem, return exactly: INVALID
"""

import json
import ast
from groq import Groq
import groq

from .groq import CODING_MODELS
from ..misc.debug import delayed
from ..gui.logger import load_page_logged
from .llm_retry import retry_on_rate_limit
from config.apikey import GROQ_API_KEY

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
            temperature=0.1,
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
    def correct(self, problem_details: str, project: dict, max_loops=5) -> dict:
        returned_value = None

        for loop_id in range(max_loops):
            try:
                returned_value = self.try_correct(problem_details, project)
                return json.loads(returned_value)
            except groq.RateLimitError as e:
                return {"RateLimitError.err": repr(e)}
            except groq.APIStatusError as e:
                if loop_id == max_loops - 1:
                    return {"APIStatusError.err": repr(e)}
                
                self.model_id = -1
                returned_value = self.try_correct(problem_details, project)
                self.model_id = 1
                return json.loads(returned_value)
            except Exception as error:
                print(error)
                self.swap_model()

        returned_value = self.try_correct(problem_details, project)
        return json.loads(returned_value)