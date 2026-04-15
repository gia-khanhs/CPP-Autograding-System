from groq import Groq

from config.apikey import GROQ_API_KEY
from .llm_retry import retry_on_rate_limit


CODING_MODELS = ["moonshotai/kimi-k2-instruct-0905",
                 "moonshotai/kimi-k2-instruct",
                 "groq/compound-mini"]

CLASSIFIER_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct",
                     "llama-3.3-70b-versatile"]

class APICaller:
    client = Groq(api_key=GROQ_API_KEY)

    def __init__(self, model="moonshotai/kimi-k2-instruct-0905") -> None:
        self.model = model

    @retry_on_rate_limit()
    def generate(self, user_prompt: str) -> str:
        chat_completion = APICaller.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=self.model
        )

        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {self.model}")

        return returned_content
    
    @retry_on_rate_limit()
    def instructed_generate(self, system_prompt: str, user_prompt: str) -> str:
        chat_completion = APICaller.client.chat.completions.create(
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
            model=self.model,
            max_completion_tokens=8192
        )

        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {self.model}")

        return returned_content
    
class LLMWebSearcher:
    client = Groq(api_key=GROQ_API_KEY)

    def __init__(self, model="groq/compound-mini") -> None:
        self.model = model

    @retry_on_rate_limit()
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        chat_completion = LLMWebSearcher.client.chat.completions.create(
            model=self.model,
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
            tool_choice="auto",
            # tool_choice="required",
            # tools=[
            #     {"type": "browser_search"}
            # ],
            temperature=0.0
        )

        returned_content = chat_completion.choices[0].message.content

        if returned_content is None:
            raise LookupError(f"Cannot get the response from {self.model}")

        return returned_content