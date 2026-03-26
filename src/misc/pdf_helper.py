from pathlib import Path
import re
from typing import cast, Any

import pymupdf

from .debug import logged
from .text_helper import beautify_text

def read_pdf(pdf_path: Path):
    full_text = []

    with pymupdf.open(pdf_path) as pdf_doc:
        for page in pdf_doc:
            clip = pymupdf.Rect(page.rect)
            clip.y1 -= 50

            text = page.get_text("text", clip=clip, sort=True)

            full_text.append(text)
            full_text.append("\n")

    full_text = "\n".join(full_text)
    full_text = re.sub(r"([^;\n])(\n)", r"\1 ", full_text)
    full_text = beautify_text(full_text)

    return full_text


def read_bold_text(pdf_path: Path) -> list[str]:
    pdf_doc = pymupdf.open(pdf_path)
    bold_text_list = []
    
    for page in pdf_doc:
        blocks = cast(dict[str, Any], page.get_text("dict"))
        
        try:
            blocks = blocks["blocks"]
        except:
            raise KeyError("Can not get text blocks of the pdf!")

        for block in blocks:
            if not "lines" in block:
                continue
                
            block_text = []

            for line in block["lines"]:
                for span in line["spans"]:
                    # if span["flags"] & pymupdf.TEXT_FONT_BOLD:
                    if span["size"] > 15 and span["size"] < 25:
                        block_text.append(span["text"])

            bold_text_list.append(" ".join(block_text))

    bold_text_list = [beautify_text(text)
                      for text in bold_text_list
                      if text]
    return bold_text_list