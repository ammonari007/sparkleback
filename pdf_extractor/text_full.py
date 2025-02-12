import argparse
import os
import sys
import time
import bisect
import fitz
import pymupdf
from typing import List

from utils.clean_text import clean_text
from pdf_extractor.ocr_illegible import has_invalid_chars, ocr_text
from pdf_extractor.parse_table import ParseTab

FLAGS = (pymupdf.TEXT_CID_FOR_UNKNOWN_UNICODE | pymupdf.TEXT_DEHYPHENATE |
         pymupdf.TEXT_INHIBIT_SPACES | pymupdf.TEXT_PRESERVE_LIGATURES)


def get_table_bboxes(page):
    tables = page.find_tables()
    if not len(tables):
        return []
    else:
        return tables.tables


def recoverpix(doc, item):
    """Return image for a given XREF."""
    x = item[0]  # xref of PDF image
    s = item[1]  # xref of its /SMask
    if s == 0:  # no smask: use direct image output
        return doc.extract_image(x)

    def getimage(pix):
        if pix.colorspace.n != 4:
            return pix
        tpix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        return tpix

    # we need to reconstruct the alpha channel with the smask
    pix1 = pymupdf.Pixmap(doc, x)
    pix2 = pymupdf.Pixmap(doc, s)  # create pixmap of the /SMask entry

    """Sanity check:
    - both pixmaps must have the same rectangle
    - both pixmaps must have alpha=0
    - pix2 must consist of 1 byte per pixel
    """
    if not (pix1.irect == pix2.irect and pix1.alpha == pix2.alpha == 0 and pix2.n == 1):
        print("Warning: unsupported /SMask %i for %i:" % (s, x))
        print(pix2)
        pix2 = None
        return getimage(pix1)  # return the pixmap as is

    pix = pymupdf.Pixmap(pix1)  # copy of pix1, with an alpha channel added
    pix.set_alpha(pix2.samples)  # treat pix2.samples as the alpha values
    pix1 = pix2 = None  # free temp pixmaps

    # we may need to adjust something for CMYK pixmaps here:
    return getimage(pix)


def extract_objects(page):
    """Extract images and / or fonts from a PDF."""
    image_xrefs = set()  # already saved images
    image_data = []
    itemlist = page.get_page_images()
    for item in itemlist:
        xref = item[0]
        if xref not in image_xrefs:
            image_xrefs.add(xref)
            pix = recoverpix(doc, item)
            if type(pix) is dict:
                imgdata = pix["image"]
            else:
                pix = (
                    pix
                    if pix.colorspace.n < 4
                    else pymupdf.Pixmap(pymupdf.csRGB, pix)
                )

            image_data.append((pix, imgdata, xref, item))
    return image_data


def page_layout(page):
    left = page.rect.width  # left most used coordinate
    right = 0  # rightmost coordinate
    rowheight = page.rect.height  # smallest row height in use
    chars = []  # all chars here
    rows = set()  # bottom coordinates of lines
    GRID = 2
    fontsize = 3
    # --------------------------------------------------------------------

    def curate_rows(rows):
        """Make list of integer y-coordinates of lines on page.

        Coordinates will be ascending and differ by 'GRID' points or more."""
        rows = list(rows)
        rows.sort()  # sort ascending
        nrows = [rows[0]]
        for h in rows[1:]:
            if h >= nrows[-1] + GRID:  # only keep significant differences
                nrows.append(h)
        return nrows  # curated list of line bottom coordinates

    # --------------------------------------------------------------------
    def find_line_index(values: List[int], value: int) -> int:
        """Find the right row coordinate (using bisect std package).

        Args:
            values: (list) y-coordinates of rows.
            value: (int) lookup for this value (y-origin of char).
        Returns:
            y-ccordinate of appropriate line for value.
        """
        i = bisect.bisect_right(values, value)
        if i:
            return values[i - 1]
        return None

    # --------------------------------------------------------------------
    def make_lines(chars):
        lines = {}  # key: y1-ccordinate, value: char list
        for c in chars:
            ch, ox, oy, cwidth = c
            y = find_line_index(rows, oy)  # index of origin.y
            lchars = lines.get(y, [])  # read line chars so far
            lchars.append(c)
            lines[y] = lchars  # write back to line

        # ensure line coordinates are ascending
        keys = list(lines.keys())
        keys.sort()
        return lines, keys

    # --------------------------------------------------------------------
    def compute_slots(keys, lines, right, left):
        """Compute "char resolution" for the page.

        The char width corresponding to 1 text char position on output - call
        it 'slot'.
        For each line, compute median of its char widths. The minimum across
        all "relevant" lines is our 'slot'.
        The minimum char width of each line is used to determine if spaces must
        be inserted in between two characters.
        """
        slot = used_width = right - left
        lineslots = {}
        for k in keys:
            lchars = lines[k]  # char tuples of line
            ccount = len(lchars)  # how many
            if ccount < 2:  # if short line, just put in something
                lineslots[k] = (1, 1, 1)
                continue
            widths = [c[3] for c in lchars]  # list of all char widths
            widths.sort()
            line_width = sum(widths)  # total width used by line
            i = int(ccount / 2 + 0.5)  # index of median
            median = widths[i]  # take the median value
            if (
                line_width / used_width >= 0.3 and median < slot
            ):  # if line is significant
                slot = median  # update global slot
            lineslots[k] = (widths[0], median, widths[-1])  # line slots
        return slot, lineslots

    # --------------------------------------------------------------------
    def joinligature(lig):
        """Return ligature character for a given pair / triple of characters.

        Args:
            lig: (str) 2/3 characters, e.g. "ff"
        Returns:
            Ligature, e.g. "ff" -> chr(0xFB00)
        """
        if lig == "ff":
            return chr(0xFB00)
        elif lig == "fi":
            return chr(0xFB01)
        elif lig == "fl":
            return chr(0xFB02)
        elif lig == "ft":
            return chr(0xFB05)
        elif lig == "st":
            return chr(0xFB06)
        elif lig == "ffi":
            return chr(0xFB03)
        elif lig == "ffl":
            return chr(0xFB04)
        return lig

    # --------------------------------------------------------------------
    def process_blocks(page):
        left = page.rect.width  # left most used coordinate
        right = 0  # rightmost coordinate
        rowheight = page.rect.height  # smallest row height in use
        chars = []  # all chars here
        rows = set()  # bottom coordinates of lines
        blocks = page.get_text("rawdict", flags=FLAGS)["blocks"]
        for block in blocks:
            for line in block["lines"]:
                if line["dir"] != (1, 0):  # ignore non-horizontal text
                    continue
                x0, y0, x1, y1 = line["bbox"]
                if y1 < 0 or y0 > page.rect.height:  # ignore if outside CropBox
                    continue
                # upd row height
                height = y1 - y0

                if rowheight > height:
                    rowheight = height
                for span in line["spans"]:
                    if span["size"] <= fontsize:
                        continue
                    for c in span["chars"]:
                        ch = c["c"]
                        if has_invalid_chars(c):
                            ch = ocr_text(c)
                        x0, _, x1, _ = c["bbox"]
                        cwidth = x1 - x0
                        ox, oy = c["origin"]
                        oy = int(round(oy))
                        rows.add(oy)
                        if left > ox and ch != " ":
                            left = ox  # update left coordinate
                        if right < x1:
                            right = x1  # update right coordinate
                        # handle ligatures:
                        if cwidth == 0 and chars != []:  # potential ligature
                            old_ch, old_ox, old_oy, old_cwidth = chars[-1]
                            if old_oy == oy:  # ligature!
                                if old_ch != chr(0xFB00):  # previous "ff" char lig?
                                    lig = joinligature(old_ch + ch)  # 2-char
                                # convert to one of the 3-char ligatures:
                                elif ch == "i":
                                    lig = chr(0xFB03)  # "ffi"
                                elif ch == "l":
                                    lig = chr(0xFB04)  # "ffl"
                                else:  # something wrong, leave old char in place
                                    lig = old_ch
                                chars[-1] = (lig, old_ox, old_oy, old_cwidth)
                                continue
                        chars.append((ch, ox, oy, cwidth))  # all chars on page
        return rows, chars, rowheight, left, right

    # --------------------------------------------------------------------
    def make_textline(left, slot, lineslots, lchars):
        """Produce the text of one output line.

        Args:
            left: (float) left most coordinate used on page
            slot: (float) avg width of one character in any font in use.
            minslot: (float) min width for the characters in this line.
            chars: (list[tuple]) characters of this line.
        Returns:
            text: (str) text string for this line
        """
        minslot, median, maxslot = lineslots
        text = ""  # we output this
        old_x1 = 0  # end coordinate of last char
        old_ox = 0  # x-origin of last char
        if minslot <= pymupdf.EPSILON:
            raise RuntimeError(
                "program error: minslot too small = %g" % minslot)
        for c in lchars:  # loop over characters
            char, ox, _, cwidth = c
            ox = ox - left  # its (relative) start coordinate
            x1 = ox + cwidth  # ending coordinate
            # eliminate overprint effect
            if (
                old_ox <= ox < old_x1
                and char == text[-1]
                and ox - old_ox <= cwidth * 0.2
            ):
                continue

            # omit spaces overlapping previous char
            if char == " " and (old_x1 - ox) / cwidth > 0.8:
                continue

            # close enough to previous?
            if ox < old_x1 + minslot:  # assume char adjacent to previous
                text += char  # append to output
                old_x1 = x1  # new end coord
                old_ox = ox  # new origin.x
                continue

            # else next char starts after some gap:
            # fill in right number of spaces, so char is positioned
            # in the right slot of the line
            delta = int(ox / slot) - len(text)
            if delta > 1 and ox <= old_x1 + slot * 2:
                delta = 1
            if ox > old_x1 and delta >= 1:
                text += " "
            # now append char
            text += char
            old_x1 = x1  # new end coordinate
            old_ox = ox  # new origin
        return text.rstrip()
    # extract page text by single characters ("rawdict")
    rows, chars, rowheight, left, right = process_blocks(page)
    if rows == set():
        return ''
    # compute list of line coordinates - ignoring small (GRID) differences
    rows = curate_rows(rows)

    # sort all chars by x-coordinates, so every line will receive
    # them sorted.
    chars.sort(key=lambda c: c[1])

    # populate the lines with their char tuples
    lines, keys = make_lines(chars)

    slot, lineslots = compute_slots(keys, lines, right, left)

    # compute line advance in text output
    text = ""
    rowheight = rowheight * (rows[-1] - rows[0]) / \
        (rowheight * len(rows)) * 1.5
    rowpos = rows[0]  # first line positioned here
    for k in keys:  # walk through the lines
        while rowpos < k:  # honor distance between lines
            text += "\n"
            rowpos += rowheight
        textline = make_textline(left, slot, lineslots[k], lines[k])
        parsed_textline = (textline + "\n").encode("utf8",
                                                   errors="surrogatepass")
        text += parsed_textline.decode()
        rowpos = k + rowheight

    return text


def gettext(page):
    text = page_layout(page)
    return clean_text(text)
