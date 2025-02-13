from bs4 import BeautifulSoup
import re
from utils.clean_text import join_sentences


def html_to_text(html_str):
    """Master fn for cleaning HTML string"""
    if not html_str or not len(html_str):
        return ''
    soup = BeautifulSoup(html_str.replace("\/", "/"), 'html.parser')
    soup = add_newlines(tables_to_text(clear_useless_html(soup)))
    return join_sentences([sent for sent in soup.strings])


def is_html_str(string):
    return bool(BeautifulSoup(string.replace("\/", "/"), "html.parser").find())


def parse_html_table(table):
    headers = [th.text.lower().strip()
               for th in table.find_all("tr")[0].find_all(['th', "td"])]
    html_rows = table.find_all('tr')[1:]
    rows = []
    for row in html_rows:
        row_text = ""
        cells = [td.text.strip() for td in row.find_all('td')]
        row_text = "- Row " + str(html_rows.index(row) + 1) + ": "
        for i in range(0, len(cells)):
            if i < len(headers) and len(headers[i]):
                row_text += headers[i] + " = " + cells[i] + ", "
            else:
                row_text += cells[i] + ", "
        rows.append(row_text[0:-2])
    rows_text = "(Tabular data as an ordered, bulleted list of sentences, where each sentence represents a single table row as a comma-separated list of its values for each column (attribute) in the table.)\n" + "\n".join(rows) + ". "
    return rows_text


def tables_to_text(soup: BeautifulSoup):
    for table in soup.find_all("table"):
        table.replace_with(parse_html_table(table))
    return soup


def clear_useless_html(soup: BeautifulSoup):
    useless_tags = ["strong", "b", "hr", "small", "strike",
                    "em", "center", "i", "u", "sub", "template", "sup"]
    for tag in useless_tags:
        for elem in soup.find_all(tag):
            elem.unwrap()
    return soup


def add_newlines(soup: BeautifulSoup):
    for p in soup.find_all("p"):
        p_html = str(p)
        p.replace_with(BeautifulSoup(
            "<br />" + p_html + "<br />", 'html.parser'))
    for br in soup.find_all("br"):
        br.replace_with("\n")
    return soup
