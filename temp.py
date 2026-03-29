from __future__ import annotations

import json
import re
from html import unescape
from typing import Any

from bs4 import BeautifulSoup
from curl_cffi import requests


def get_webpage_content(
    url: str,
    timeout: int = 30,
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

    # Remove obvious noise
    for tag in soup(["script", "style", "noscript", "svg", "img", "iframe"]):
        tag.decompose()

    # First try the most likely content containers
    candidate_selectors = [
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

    # Then try structured data blobs
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

    # Then fall back to the whole body
    body = soup.body or soup
    text = _clean_text(body.get_text("\n", strip=True))

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
    return text.strip()

def decode_to_plain_text(text: str) -> str:
    text = text.rstrip("\\")
    text = text.encode("utf-8").decode("unicode_escape")
    text = unescape(text)
    return BeautifulSoup(text, "html.parser").get_text("\n", strip=True)