import os

from groq import Groq

from config.apikey import GROQ_API_KEY
from ..misc.debug import delayed
from .llm_retry import retry_on_rate_limit

client = Groq(api_key=GROQ_API_KEY)

@retry_on_rate_limit()
def detect_injection(prompt: str, threshold: float = 0.7) -> bool:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="meta-llama/llama-prompt-guard-2-86m",
    )


    prob = chat_completion.choices[0].message.content

    if prob is None:
        return False
    
    prob = float(prob)
    print(prob)
    if prob >= threshold:
        print(prob)
        return True
    
    return False
