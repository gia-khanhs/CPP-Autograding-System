from ..misc.debug import delayed
from ..gui.logger import load_page_logged
from .llm_retry import retry_on_rate_limit
from config.apikey import GROQ_API_KEY

from groq import Groq

class CompoundCaller:
    client = Groq(api_key=GROQ_API_KEY)

    def __init__(self, model="groq/compound-mini") -> None:
        self.model = model

    @retry_on_rate_limit()
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        chat_completion = CompoundCaller.client.chat.completions.create(
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

# region llm api web search
oss_20b = CompoundCaller("groq/compound-mini")
search_instruction = "You are given an url to an online judger for a coding problem. Do a web search and return only the exact problem statement. Return the original URL if you cannot get the problem statement."

@retry_on_rate_limit()
@load_page_logged
def get_problem_statement(url: str):
    statement = oss_20b.generate(search_instruction, url)
    return statement
#endregion