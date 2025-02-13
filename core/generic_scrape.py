from copy import deepcopy
from trafilatura import extract
from trafilatura.settings import DEFAULT_CONFIG
import urllib
import json
import ssl
from bs4 import BeautifulSoup
import re
import urllib.request
from utils.clean_html import html_to_text

ssl._create_default_https_context = ssl._create_unverified_context


def get_url_proxied(url):
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'http': 'http://brd-customer-hl_c7d4671e-zone-demo_test:2rjhfl92aobr@brd.superproxy.io:22225',
                                        'https': 'http://brd-customer-hl_c7d4671e-zone-demo_test:2rjhfl92aobr@brd.superproxy.io:22225'}))
        return opener.open(url).read()
    except Exception as e:
        return None


def clean_url(url):
    if url and len(url):
        url = url.lower()[0:-1] if url[-1] == "/" else url.lower()
        url = re.sub(r"^(https?:\/\/)?(www\.)?", "https://www.", url)
        return urllib.urldefrag(url).geturl()
    else:
        return None


def override_settings():
    my_config = deepcopy(DEFAULT_CONFIG)
    my_config['DEFAULT']['MIN_EXTRACTED_SIZE'] = '100'
    my_config['DEFAULT']['MIN_OUTPUT_SIZE'] = '100'
    my_config['DEFAULT']['MIN_EXTRACTED_COMM_SIZE'] = '10'
    my_config['DEFAULT']['MIN_OUTPUT_COMM_SIZE'] = '10'
    my_config['DEFAULT']['MIN_DUPLCHECK_SIZE'] = '10'
    my_config['DEFAULT']['MAX_REPETITIONS'] = '0'
    my_config['DEFAULT']['EXTENSIVE_DATE_SEARCH'] = 'off'
    my_config['DEFAULT']['EXTRACTION_TIMEOUT'] = '0'
    return my_config


def scrape_article_url(url, with_links=False, with_images=False):
    """Master Function"""
    html = get_url_proxied(url)
    if html:
        try:
            soup = BeautifulSoup(html, 'html.parser')
            return get_text(html, url)
        except:
            return ''
    else:
        return ''


def get_article_source_category(url):
    news_urls = ["forbes", "bloomberg", "variety", "cnn", "nbc", "fox", "daily", "mirror",
                 "times", "bbc", "skynews", "wallstreet", "abc", "post", "losangeles", "reuters", "huffpost",
                 "guardian", "usa", "npr", "espn", "ft", "press", "news", "radar", "business", "gazette", "star",
                 "reporter", "magazine", "mail", "msn", "paper", "eagle", "agency", "express", "world", "mundo",
                 "room", "gadget", "week", "verge", "mag", "trends", "idealista", "tmz", "journal", "today", "interview"]
    social_urls = ["instagram", "facebook", "twitter", "tiktok", "pinterest"]
    forum_urls = ["forum", "reddit", "post", "comments", "group", "twitter"]
    ecommerce_review_urls = ["reviews", "review",
                             "product", "products", "testimonial", "feedback"]
    blog_urls = ["medium", "blog", "notion",
                 "tumblr", "wordpress", "feather", "bloq"]
    if url in news_urls:
        return "news"
    elif url in blog_urls:
        return "blog"
    else:
        return "information_page"


def get_text(html, url):
    try:
        text_obj = extract(
            html,
            url=url,
            favor_precision=True,
            favor_recall=True,
            include_comments=False,
            include_tables=True,
            include_formatting=True,
            deduplicate=True,
        )
        return html_to_text(text_obj)
    except Exception as e:
        return ''


def del_unnecessary_keys(key_names: list[str] | str, obj):
    if isinstance(key_names, str):
        key_names = [key_names]
    for key_name in key_names:
        if key_name in obj.keys():
            del obj[key_name]
    return obj


def get_external_links(soup, domain):
    links = soup.find_all(
        "a", href=lambda href: href and not domain in href and href[0] != "#" and href[0] != "/" and not "mailto" in href and not "javascript" in href.lower())
    uniq_urls = []
    for link in links:
        u = clean_url(link.get("href"))
        ut = str(link.text)
        if "powered by shopify" in ut.lower():
            continue
        if not len(ut):
            parents = link.find_parents()
            if len(parents):
                for parent in parents:
                    if parent.name in ["h1", "h2", "h3"] and not len(ut):
                        ut = str(parent.text)
                        break
                    else:
                        if len(list(parent.descendants)):
                            for p in parent.descendants:
                                if p.name in ["h1", "h2", "h3"] and not len(ut):
                                    ut = str(p.text)
                                    break
                    if len(ut):
                        break
        if not len([i for i in uniq_urls if i[0] == u]):
            uniq_urls.append((u, ut))
    return uniq_urls


def get_images(soup):
    images = soup.find_all("img")
    img_types = ["jpg", "jpeg", "png"]
    imgs = []
    for img in images:
        srcs = [img.attrs[attr]
                for attr in img.attrs if
                img.attrs[attr]
                and not "logo" in img.attrs[attr] and not "LOGO" in img.attrs[attr]
                and not "icon" in img.attrs[attr] and not "ICON" in img.attrs[attr]
                and not "noun" in img.attrs[attr] and not "NOUN" in img.attrs[attr]
                and any(i for i in img_types if i in img.attrs[attr])]
        srcs = ["https://" + i[2:] for i in srcs if i[0:2] == "//"] + ["https://" + i[1:]
                                                                       for i in srcs if i[0] == "/" and i[1] != "/"]
        if len(srcs):
            src = srcs[0].split(" ")[0]
            if not src.lower().replace("mobile", "").replace("desktop", "") in [i.lower().replace("mobile", "").replace("desktop", "") for i in imgs]:
                imgs.append(src)
    return list(set(imgs))


def clean_text_further(text):
    keywords = ["customer support", "buy", "checkout", "delivery", "shipping", "interest", "update",
                "account", "shop", "collection", "faq", "search", "help", "click here",
                "subscribe", "free trial", "login", "signup", "logout", "sign in", "sign up",
                "log in", "log out", "sign out", "advertisement", "promotion", "discount", "sale",
                "written by", "authored by", "skip", "join", "follow", "link", "find out", "read more",
                "contact", "question", "reply", "terms", "conditions", "agreement", "you agree", "cookies"
                "personal data", "track your", "feedback", "email", "your data", "refer", "copyright",
                "all rights reserved", "unsubscribe", "manage your", "password", "this website", "not now",
                "notifications", "allow", "ads", "close", "hide", "register", "view more", "unlock", "get access",
                "free", "learn more", "show more", "tell me more", "block", "details", "basket", "cart", "order",
                "policy", "add to", "remove from", "see more", "accept", "decline", "deny", "save", "bookmark",
                "favorite", "chat", "search", "sell", "transact", "pay", "purchase", "loading", "please wait"]
    sents = [t for t in text.split("\n") if not (len(t.split(" ")) < 6 and any(
        [k for k in keywords if k in t.lower()]))]
    return "\n".join(sents).replace("\u2019", "'")
