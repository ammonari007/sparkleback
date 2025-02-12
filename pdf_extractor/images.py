import os
import sys

import fitz

doc = fitz.open()  # output PDF
img_folder = sys.argv[1]  # example: image folder name provided
dirname = os.path.dirname(img_folder)
img_list = os.listdir(img_folder)  # some list of image filenames


def process_image(bbox):

    pix = fitz.Pixmap(imgfile)  # make a pixmap form the image file
    # 1-page PDF with the OCRed image
    pdfbytes = pix.pdfocr_tobytes(language="eng")
    imgpdf = fitz.open("pdf", pdfbytes)  # open it as a PDF
    doc.insert_pdf(imgpdf)  # append the image page to output


doc.ez_save("ocr-pdf.pdf")  # save output


def is_image(bb):
    return bb["type"] == 1
