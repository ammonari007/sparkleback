from sal.src.process_pdfs import list_files
from core.brightdata import google_search
from core.generic_scrape import scrape_article_url
import json

ops = []
ops_ = {}


def op_search(query):
    results = google_search(search_key, None, 5)
    urls = []
    articles = []
    if results and len(results):
        for r in results:
            url = r.get("link", None)
            if not url in urls:
                text = scrape_article_url(url)
                if text and len(text):
                    articles.append(text)
                    urls.append(url)
                    print(
                        f"Scraped article of length {len(text)}, total articles {len(articles)} out of {len(results)}")
    print(articles)
    return articles


def scrape_ops_info():
    all_files = list_files("sal/etl_data/", "json")
    all_data = []
    all_ops = []
    for path in all_files:
        path_idx = all_files.index(path)
        print(f"Working on path {path}")
        data = None
        with open(path) as f:
            data = json.loads(json.load(f))
        opptys = data["opportunities"]
        for opp in opptys:
            opp_idx = opptys.index(opp)
            name = opp["name"]
            org = opp["organization"]
            search_key = f""" "{name}" "{org}" funding criteria application" """
            text = op_search(search_key)
            other = "\n\n".join(
                ["".join(v) if isinstance(v, list) else v for v in opp.values() if not v in [name, org]])
            other += "\n\n".join(text)
            print(len(other))
            with open(f"sal/src/{path_idx}{opp_idx}.txt", "w") as f:
                f.write(other)
            all_data.append(other)
    with open("sal/etl_data/all_ops.json", "w") as f:
        f.write(json.dumps({"ops": all_data}))


def update_ops():
    all_files = list_files("sal/etl_data/", "json")
    all_data = []
    all_ops = []
    for path in all_files:
        path_idx = all_files.index(path)
        print(f"Working on path {path}")
        data = None
        with open(path) as f:
            data = json.loads(json.load(f))
        opptys = data["opportunities"]
        for opp in opptys:
            opp_idx = opptys.index(opp)
            name = opp["name"]
            org = opp["organization"]
            all_ops.append({"name": name, "org": org,
                           "path": f"sal/src/{path_idx}{opp_idx}.txt"})
    with open("sal/etl_data/all_ops.json", "w") as f:
        f.write(json.dumps({"ops": all_ops}))
