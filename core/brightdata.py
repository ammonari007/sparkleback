import json
import requests
import urllib.parse

######## Building Params for Search URL ##########


def search_type_param(search_type: str) -> tuple[str, str | None]:
    allowed_search_types = {
        "images": "isch", "shopping": "shop", "news": "nws", "videos": "vid"}
    if not search_type or not len(search_type) or not search_type in list(allowed_search_types.keys()):
        return ("tbm", None)  # This is just a normal google search
    else:
        return ("tbm", allowed_search_types[search_type])


def num_results_param(num_urls: int) -> tuple[str, int]:
    return ("num", num_urls)


def time_range_param(time_range: str = "30 days") -> tuple[str, str | None]:
    date = None
    allowed_time_ranges = {"hour": "now 1-H", "4 hours": "now 4-H", "day": "now 1-d",
                           "7 days": "now 7-d", "30 days": "today 1-m", "90 days": "today 3-m", "year": "today 12-m"}
    if not time_range in list(allowed_time_ranges.keys()):
        date = "today 1-m"
    else:
        date = allowed_time_ranges[time_range]
    return ("date", date)


def google_cat_param(cat: str = "all categories") -> tuple[str, int]:
    cat_id = 0
    with open("google_cats.json") as f:
        cats = json.load(f)
        matches = [i["id"] for i in cats if i["name"].lower(
        ) in cat.lower() or cat.lower() in i["name"].lower()]
        if matches and len(matches):
            matches.sort()
            cat_id = matches[0]

        return ("cat", cat_id)


def encode_url_params(url_params: dict[str, str | int]) -> str:
    return urllib.parse.urlencode(url_params) + "&brd_json=1"


######## Building Search URL ##########


def search_by_image_url(image_url: str) -> str:
    return f"https://www.google.com/searchbyimage?image_url={image_url}&download=0&brd_json=1"


def search_url(query: str, search_type: str = None, num_results: int = 10) -> str:
    uule = "London Borough of Lambeth,England,United Kingdom"
    params = {
        "q": query,
        "gl": "gb",
        "uule": uule
    }
    num_results_key, num_results_value = num_results_param(num_results)
    params[num_results_key] = num_results_value

    search_key, search_val = search_type_param(search_type)
    if search_val:
        params[search_key] = search_val

    return "https://www.google.com/search?" + encode_url_params(params)

######## Making BrightData request ##########


def build_proxies() -> dict[str, str]:
    host = 'brd.superproxy.io'
    port = 33335
    username = 'brd-customer-hl_c7d4671e-zone-serp_api1'
    password = '8eiy06nzlp6a'
    proxy_url = f'http://{username}:{password}@{host}:{port}'
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def send_request(google_url: str) -> dict | list | Exception:
    proxies = build_proxies()
    try:
        response = requests.get(google_url, proxies=proxies, verify=False)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in processing Google request: {e}")
        return None

######## Top Level Requests ##########


def google_search(query: str, search_type: str = None, num_results: int = 20) -> dict | list | Exception | None:
    if not query:
        print(f"No query param provided")
        return None
    url = search_url(query, search_type, num_results)
    print(url)
    if url:
        response = send_request(url)
        if response and "organic" in response:
            return response["organic"]
        else:
            return None
    else:
        print("Something went wrong with your search params. Try again")
        return None
