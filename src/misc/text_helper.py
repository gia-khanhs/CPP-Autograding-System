import re
from typing import overload, Literal

def beautify_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+([,.])", r"\1", text)

    return text


def split_lines(text: str) -> list[str]:
    return text.splitlines()


def join_lines(text: list[str]) -> str:
    joined_text = "\n".join(text)
    return joined_text


def remove_space(text: list[str] | str) -> list[str] | str:
    if isinstance(text, list):
        text = ["".join(line.split())
                for line in text]
    else:
        text = "".join(text.split())

    return text

def find_urls(text: str) -> list[str]:
    urls = re.findall(r"(https?://\S+)", text)

    return urls