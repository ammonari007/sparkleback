import io
import fitz
import numpy as np
import pandas as pd
from rapidocr_onnxruntime import RapidOCR
from utils.clean_html import html_to_text


def parse_pdf(self, file) -> list[dict]:
    doc = make_fitz_doc(file)
    if not doc:
        return ""
    extracted = []

    for page in doc:
        tables = self._extract_tables(page)
        images = self._extract_images(page, doc)

        extracted_text = page.get_text("text", sort=True)
        text = [{
            'page_content': extracted_text,
            'metadata': {"page": page.number + 1, "type": "text"},
        }]

        if isinstance(file, str):
            path = file.split("/")[-1]
            text[0]["metadata"]["source"] = path

        extracted += text + tables + images

    return extracted


def is_noisy_table(df: pd.DataFrame) -> bool:
    if df is None or df.empty or all(df.isnull().all()):
        return True
    # Drop df with minimum shape critera
    n_rows, n_cols = df.shape
    if n_rows <= 1 and n_cols <= 1:
        return True
    return False


def image_to_text_ocr(image) -> str:
    image_buffer = np.frombuffer(image.samples, dtype=np.uint8)
    image_buffer = image_buffer.reshape(image.height, image.width, -1)
    ocr = RapidOCR()
    extracted, _ = ocr(image_buffer)
    if not extracted:
        return None
    text = [s[1] for s in extracted]
    return " ".join(text)


def _chunk_df(df: pd.DataFrame, chunk_size: int) -> list[pd.DataFrame]:
    return [df[i: i + chunk_size] for i in range(0, df.shape[0], chunk_size)]


def _clean_df(df):
    df = df.replace("", None)
    return df


def make_fitz_doc(file):
    if isinstance(file, io.BytesIO) or isinstance(file, bytes):
        return fitz.open(stream=file, filetype=self.file_type)
    elif isinstance(file, str):
        return fitz.open(filename=file, filetype=self.file_type)
    else:
        return None


def extract_tables(page) -> list[dict]:
    try:
        tabs = page.find_tables()
        if not tabs or len(tabs):
            return []
        tables = tabs.tables
    except Exception as e:
        return []

    table_text = []

    for table in tables:
        df = table.to_pandas().replace("", None)
        if is_noisy_table(df):
            continue
        clean_text = make_fitz_doc(df.to_html())
        extracted.append(
            {'page_content': df_html, 'metadata': meta_data})

        page.add_redact_annot(table.bbox)

    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

    return extracted


def extract_images(page, doc) -> list[dict]:
    try:
        images = page.get_images()
        if not images:
            return []
    except Exception as e:
        print(f"Skipping page image extraction, exception raised: {e}")
        return []

    extracted = []
    for image in images:
        pix_map = fitz.Pixmap(doc, image[0])
        try:
            text = image_to_text_ocr(pix_map)
        except Exception as e:
            print(
                f"error extracting image on {page.number} - skipping image: {e}"
            )
            continue

        if text and len(text):
            extracted.append(text)

    return extracted


class FileParserABC(ABC):
    @abstractmethod
    def extract(self, file) -> list[dict]:
        pass


class PdfParser(FileParserABC):
    def __init__(self, extract_tables: bool, extract_images: bool) -> None:
        self.extract_tables = extract_tables
        self.extract_images = extract_images
        self.file_type = "pdf"

        # Table extractor;
        self.chunk_size = 50
        self.max_missing_pct = 0.2
        self.min_cols = 1
        self.min_rows = 1

    def extract(self, file) -> list[dict]:
        """
        Parses each page of the pdf sequentially, extracting text, images and tables if sepcified
        in the constructor. Returns a list of Documents containing metadata eg. page_number.
        """
        if isinstance(file, io.BytesIO) or isinstance(file, bytes):
            doc = fitz.open(stream=file, filetype=self.file_type)
        elif isinstance(file, str):
            doc = fitz.open(filename=file, filetype=self.file_type)
        else:
            raise TypeError(
                "file must be of type `io.BytesIO` or `pathlib.Path`")

        extracted = []

        for page in doc:
            tables = self._extract_tables(page)
            images = self._extract_images(page, doc)

            extracted_text = page.get_text("text", sort=True)
            text = [{
                'page_content': extracted_text,
                'metadata': {"page": page.number + 1, "type": "text"},
            }]

            if isinstance(file, str):
                path = file.split("/")[-1]
                text[0]["metadata"]["source"] = path

            extracted += text + tables + images

        return extracted

    def _extract_tables(self, page) -> list[dict]:
        """
        Internal method to extract tables at a page level and converts to text.
        Following steps:
            - `find_tables` fitz internal.
            - `_is_noisy_table` drops noisy tables from extraction
            - Converted to HTML.
            - Chunked by `chunk_size`.
            - LLM used to covert HTML to text.
        """
        if not self.extract_tables:
            return []

        try:
            tabs = page.find_tables()
        except Exception as e:
            return []

        tables = tabs.tables
        meta_data = {"page": page.number + 1, "type": "table"}
        extracted = []

        for table in tables:
            df = table.to_pandas()
            df = _clean_df(df)
            if _is_noisy_table(df, self.max_missing_pct, self.min_cols, self.min_rows):
                continue

            # chunk to be safe
            df_chunks = _chunk_df(df, self.chunk_size)
            for df_chunk in df_chunks:
                df_html = df_chunk.to_html()
                extracted.append(
                    {'page_content': df_html, 'metadata': meta_data})

            page.add_redact_annot(table.bbox)

        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        return extracted

    def _extract_images(self, page, doc) -> list[dict]:
        """
        Internal method used to extract images at a page level using rapidOCR.
        """
        if not self.extract_images:
            return []

        try:
            images = page.get_images()
        except Exception as e:
            print(f"Skipping page image extraction, exception raised: {e}")
            return []

        extracted = []
        meta_data = {"page": page.number + 1, "type": "image"}

        if images:
            print("images")

        for image in images:
            xref = image[0]
            pix_map = fitz.Pixmap(doc, xref)
            try:
                text = _image_to_text_rapidocr(pix_map)
            except Exception as e:
                print(
                    f"error extracting image on {page.number} - skipping image: {e}"
                )
                continue

            if text:
                extracted.append({'page_content': text, 'metadata': meta_data})

        return extracted


def process_pdf(path):
    pdfparser = PdfParser(True, True)
    return pdfparser.extract(path)
