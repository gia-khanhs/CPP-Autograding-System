from .groq import LLMWebSearcher
from ..misc.debug import delayed
from ..gui.logger_backend import load_page_logged

# region llm api web search
oss_20b = LLMWebSearcher("groq/compound-mini")
search_instruction = "You are given an url to an online judger for a coding problem. Do a web search and return only the exact problem statement. Return the original URL if you cannot get the problem statement."

@delayed(delay_seconds=30)
@load_page_logged
def get_problem_statement(url: str):
    statement = oss_20b.generate(search_instruction, url)
    return statement
#endregion