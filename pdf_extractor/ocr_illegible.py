import fitz
import pymupdf

mat = pymupdf.Matrix(5, 5)  # high resolution matrix
INVALID_UNICODE = chr(0xFFFD)  # the "Invalid Unicode" character


def has_invalid_chars(char):
    return INVALID_UNICODE == char["c"]


def ocr_text(char, page):
    text = char["c"]
    if INVALID_UNICODE == text:  # invalid characters encountered!
        text1 = text.lstrip()
        sb = " " * (len(text) - len(text1))  # leading spaces
        text1 = text.rstrip()
        sa = " " * (len(text) - len(text1))  # trailing spaces
        text = sb + get_ocr_text_only(page, char["bbox"]) + sa
        return text
    else:
        return text


def get_ocr_text_only(page, bbox):
    """Return OCR-ed span text using Tesseract.

    Args:
        page: fitz.Page
        bbox: fitz.Rect or its tuple
    Returns:
        The OCR-ed text of the bbox.
    """
    # Step 1: Make a high-resolution image of the bbox.
    pix = page.get_pixmap(
        matrix=mat,
        clip=bbox,
    )
    ocrpdf = fitz.open("pdf", pix.pdfocr_tobytes())
    ocrpage = ocrpdf[0]
    text = ocrpage.get_text()
    if text.endswith("\n"):
        text = text[:-1]
    return text
