import json
from copy import deepcopy
from typing import Optional

from google import genai
from google.genai.types import GenerateContentConfigDict

from config.apikey import GEMINI_API_KEY

class LLMCaller:
    def __init__(self, api_key: str = GEMINI_API_KEY, model: str = 'gemma-3-27b-it') -> None:
        self.api_key = api_key

        self.client = genai.Client(api_key=self.api_key)
        self.model = model


    def generate(self, prompt: str, config: Optional[GenerateContentConfigDict] = None) -> Optional[str]:
        response = self.client.models.generate_content(
           model=self.model, contents=prompt, config=config
        )

        return response.text


class CodeCorrector:
    def __init__(self, llmcaller: LLMCaller) -> None:
        self.llmcaller = llmcaller

        self.system_instruction = """*You are a code correction system for university students.\n
                                    Goal:
                                    - Correct the provided code so it satisfies the problem requirements.\n
                                    Rules:
                                    - Apply the minimum necessary changes.
                                    - Preserve the original structure, formatting, and logic whenever possible.
                                    - Do not refactor, optimize, or redesign working parts.
                                    - Keep all working lines unchanged.
                                    - Only modify lines required to make the solution correct.
                                    - If the code is already correct, output it unchanged.\n
                                    Output rules:
                                    - First identify incorrect lines internally, then output corrected code only.
                                    - Do not include explanations.
                                    - Do not include comments unless they already exist in the original code.
                                    - Do not reformat the code.
                                    * The problem and code is provided below"""

        self.config: GenerateContentConfigDict  = {
                                                    # "system_instruction": self.system_instruction,
                                                    "temperature": 0.0,
                                                    "top_p": 1.0,
                                                    "top_k": 1,
                                                    "max_output_tokens": 4096,
                                                    "presence_penalty": 0.0,
                                                    "frequency_penalty": 0.0
                                                }
        
    def correct(self, prompt: str):
        final_prompt = self.system_instruction + '\n\n\n' + prompt

        return self.llmcaller.generate(final_prompt, self.config)
    
    