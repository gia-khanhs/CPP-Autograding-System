### BIG ACKNOWLEDGEMENT: THIS FILE WAS VIBE CODED AS I KNEW VERY LITTLE ABOUT WEB SCRAPING
### HOWEVER, I DID MADE GOOD EFFORT TRYING TO UNDERSTAND THIS
### I ALSO MODIFIED SOME OF THE CODE AND ADDED A NEW FUNC ON MY OWN FUNC TO EXTRACT CONTENT USING LLM

import json
import re
from typing import Any
from html import unescape
from ..llm.groq import APICaller, LLMWebSearcher
from ..misc.debug import delayed

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from bs4 import BeautifulSoup
from curl_cffi import requests

# region llm api web search
oss_20b = LLMWebSearcher("groq/compound-mini")
search_instruction = "You are given an url to an online judger for a coding problem. Do a web search and return only the exact problem statement."
@delayed
def get_problem_statement(url: str):
    statement = oss_20b.generate(search_instruction, url)
    return statement
#endregion


# region request
llama = APICaller("meta-llama/llama-4-scout-17b-16e-instruct")
instruction = """
Your task is extraction, not rewriting.

Given noisy content, remove only text that is clearly not part of the programming problem statement.

Rules:
- Do not paraphrase.
- Do not rephrase.
- Do not summarize.
- Do not reorder content.
- Do not infer missing text.
- Do not add headings or labels.
- Keep the exact original wording of the retained text.
- Join line breaks if the problem statement makes more sense afterwards.
- Only extract the original problem, do not return anything else!
"""
@delayed
def extract_problem_statement(url: str) -> str:
    # try:
    content = get_webpage_content(url)["text"]
    statement = llama.instructed_generate(instruction, content)
    # except:
        # return url

    return statement


def get_webpage_content(
    url: str,
    timeout: int = 10,
    min_text_length: int = 200,
) -> dict[str, Any]:
    response = requests.get(
        url,
        impersonate="chrome",
        timeout=timeout,
        allow_redirects=True,
        headers={
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    response.raise_for_status()

    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    for tag in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
        tag.decompose()

    candidate_selectors = [
        # SPOJ
        "#problem-body",
        "div#problem-body",
        "td.problemContent",
        "div.problem-description",

        # Codeforces
        "div.problem-statement",

        # Generic
        "article",
        "main",
        "[role='main']",
        ".problem-statement",
        ".problem-content",
        ".challenge-statement",
        ".content",
        ".container",
    ]

    for selector in candidate_selectors:
        node = soup.select_one(selector)
        if node:
            text = _clean_text(node.get_text("\n", strip=True))
            if len(text) >= min_text_length:
                return {
                    "url": str(response.url),
                    "title": title,
                    "text": text,
                    "html": html,
                    "status_code": response.status_code,
                    "content_source": f"selector:{selector}",
                }

    structured_text = _extract_from_structured_data(html)
    if len(structured_text) >= min_text_length:
        return {
            "url": str(response.url),
            "title": title,
            "text": structured_text,
            "html": html,
            "status_code": response.status_code,
            "content_source": "structured_data",
        }

    body = soup.body or soup
    text = _clean_text(body.get_text("\n", strip=True))

    if _looks_blocked(text):
        raise RuntimeError("Page looks blocked, challenge-gated, or not actually rendered.")

    if len(text) < min_text_length:
        raise RuntimeError("Could not extract meaningful content from page.")

    return {
        "url": str(response.url),
        "title": title,
        "text": text,
        "html": html,
        "status_code": response.status_code,
        "content_source": "body_fallback",
    }


def _extract_from_structured_data(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    pieces: list[str] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            _collect_text_fields(data, pieces)
        except Exception:
            continue

    for script in soup.find_all("script"):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw or len(raw) < 200:
            continue

        matches = re.findall(r'"([^"\n]{80,})"', raw)
        for match in matches[:30]:
            cleaned = _clean_text(match)
            if len(cleaned) > 100 and not _looks_like_code_or_noise(cleaned):
                pieces.append(cleaned)

    return _clean_text("\n\n".join(dict.fromkeys(pieces)))


def _collect_text_fields(obj: Any, pieces: list[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                if key.lower() in {
                    "name",
                    "headline",
                    "description",
                    "text",
                    "articlebody",
                    "body",
                }:
                    pieces.append(value)
            else:
                _collect_text_fields(value, pieces)
    elif isinstance(obj, list):
        for item in obj:
            _collect_text_fields(item, pieces)


def _clean_text(text: str) -> str:
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    
    text = text.encode('utf-8').decode('unicode_escape', "ignore")
    # text = _extra_work_for_interviewbit(text)

    return text.strip()


def _looks_blocked(text: str) -> bool:
    lowered = text.lower()
    blocked_signals = [
        "forbidden",
        "access denied",
        "verify you are human",
        "captcha",
        "enable javascript",
        "please turn javascript on",
        "request blocked",
    ]
    return any(signal in lowered for signal in blocked_signals)


def _looks_like_code_or_noise(text: str) -> bool:
    bad_signals = [
        "function(",
        "window.",
        "document.",
        "webpack",
        "__next",
        "apollo",
        "chunk",
        "use strict",
    ]
    lowered = text.lower()
    return any(signal in lowered for signal in bad_signals)

def _extra_work_for_interviewbit(text: str) -> str:
    if not "cloudfront" in text:
        return text
    
    chunks = text.split("cloudfront")
    print(chunks)

    longest_chunk_id = 0
    longest_len = 0

    for id, chunk in enumerate(chunks):
        if len(chunk) > longest_len:
            longest_len = len(chunk)
            longest_chunk_id = id

    return chunks[longest_chunk_id]
#endregion