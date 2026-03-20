from typing import Any, cast
import math


from google import genai


from src.llm.apicaller import LLMCaller
from src.misc.logger import logged
from config.apikey import GEMINI_API_KEY


def dot_product(vector1: list[float], vector2: list[float]) -> float:
    d_product = 0
    for x_i1, x_i2 in zip(vector1, vector2):
        d_product += x_i1 * x_i2

    return d_product


def vector_length(vector: list[float]) -> float:
    length = 0
    for x_i in vector:
        length += x_i ** 2
    length = math.sqrt(length)

    return length


def cosine_similarity(vector1: list[float], vector2: list[float]) -> float:
    d_product = dot_product(vector1, vector2)
    len1 = vector_length(vector1)
    len2 = vector_length(vector2)
    cosine_similarity = d_product / (len1 * len2)

    return cosine_similarity


class Embedder:
    def __init__(self, model: str = "gemini-embedding-001", api_key: str = GEMINI_API_KEY) -> None:
        self.api_client = genai.Client(api_key=api_key)
        self.model = model

    def embed(self, content: str) -> Any:
        embedding = self.api_client.models.embed_content(
            model=self.model,
            contents=content
        )
        embedding = embedding.embeddings
        if type(embedding) == list:
            embedding = embedding[0].values

        return embedding
