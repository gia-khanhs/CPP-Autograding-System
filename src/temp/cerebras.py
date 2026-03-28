import os

from cerebras.cloud.sdk import Cerebras

from config.apikey import CEREBRAS_API_KEY

class APICaller:
    client = Cerebras(
        api_key=CEREBRAS_API_KEY
    )

    def __init__(self) -> None:
        pass

    def generate(self, prompt: str):
        completion = self.client.chat.completions.create(
            messages=[{"role":"user","content": prompt}],
            model="llama3.1-8b",
            max_completion_tokens=1024,
            temperature=0.2,
            top_p=1,
            stream=False
        )

        if not hasattr(completion, "choices"):
            return None
            if not isinstance(completion.choices, list):
                return None

            return completion.choices[0].message.content
        
        return None