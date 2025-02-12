import pymupdf
import json
from pdf_extractor.text_full import gettext


def parse(path):
    doc = pymupdf.open(path)
    all_text = []
    for page in doc:
        text = gettext(page)
        if text:
            all_text.append(text)
    return "".join(all_text)


if __name__ == "__main__":
    with open("test.txt", "w") as f:
        f.write(parse("pdf_extractor/test.pdf"))
