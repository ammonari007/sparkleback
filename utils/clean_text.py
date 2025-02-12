import re


def clean_text(raw_text):
    first_clean = clean_joined_text(raw_text)
    if not first_clean:
        return ""
    sents = []
    curr_sent = ''
    for sent in first_clean.split("\n"):
        if not len(sent.strip()):
            curr_sent += "\n"
        if len(curr_sent):
            sents.append(curr_sent)
        curr_sent = sent
    sents.append(curr_sent)
    return join_sentences(list(set([s for s in sents if s and len(s)])))


def join_sentences(sents):
    body = sents[0]
    for sent in sents[1:]:
        body = add_sent(body, sent)
    return clean_joined_text(body)


def add_sent(body, sent):
    if not sent or not len(sent.strip()):
        return body
    if not body or not len(body.strip()):
        return ''
    sep_by_none_ws = (body and len(
        body) and body[-1].isspace()) or sent[0].isspace()
    sep_by_newline_newsent = len(body.strip()) and body.strip(
    )[-1] in [".", "?", "!"] and re.match(r"^\s*([\n]*)[A-Z0-9]", sent)
    sep_by_none_midsent = len(body.strip()) and body.strip()[-1] != "." and (
        re.match(r"^([\n]*)[\s\t]*", sent) or
        re.match(r"^([\n]*)[\s\t]*[\.,\?!:;\/\\\&\)@]", sent) or
        re.match(r"^([\n]*)[\s\t]*[a-zA-Z0-9]", sent)
    )
    sep_by_newline_bullets = re.match(r"^\s*(\n*)[^A-Za-z0-9,\.\&\;\:]", sent)

    if sep_by_none_midsent:
        return body + sep_by_none_midsent.group(0) + sent
    elif sep_by_none_ws:
        return body + sent
    elif sep_by_newline_newsent:
        return body + sep_by_newline_newsent.group(0) + sent
    elif sep_by_newline_bullets:
        body + sep_by_newline_bullets.group(0) + sent
    else:
        return body + " " + sent


def clean_joined_text(text):
    if not text or not len(text):
        return None
    # Remove double whitespace chars
    text = re.subn(r"\n\n\n", "\n\n", text)[0]
    # Remove whitespace between last non-whitespace char of sent and fullstop
    text = re.subn(r"[\s\n\t]*(\.|,|\?|!)", r"\1", text)[0]
    return text.strip().replace("  ", " ")
