from pathlib import Path
import re

import pymupdf

def read_pdf(file_path: Path):
    full_text = []

    with pymupdf.open(file_path) as pdf_doc:
        for page in pdf_doc:
            clip = pymupdf.Rect(page.rect)
            clip.y1 -= 50

            text = page.get_text("text", clip=clip, sort=True)

            full_text.append(text)
            full_text.append("\n")

    full_text = "\n".join(full_text)
    full_text = re.sub(r"([^;\n])(\n)", r"\1 ", full_text)

    return full_text
        

