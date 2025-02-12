from apify_client import ApifyClient
from os import getenv
from dotenv import load_dotenv

from utils.data_validation import valid_data

load_dotenv()
key = getenv("APIFY_KEY")

CLIENT = ApifyClient(key)


def run(actor_id, run_input):
    try:
        run = CLIENT.actor(actor_id).call(run_input=run_input)
        items = []
        for item in CLIENT.dataset(run["defaultDatasetId"]).iterate_items():
            is_valid, clean_item = valid_data(item)
            if is_valid:
                items.append(clean_item)
        return items
    except Exception as e:
        print(e)
        return None


def get_datasets(dataset_ids: str | list[str]):
    if not dataset_ids and not len(dataset_ids):
        return []
    dataset_id_list = [dataset_ids] if isinstance(
        dataset_ids, str) else dataset_ids
    data = []
    for d_id in dataset_id_list:
        for item in CLIENT.dataset(d_id).list_items().items:
            if not item in data:
                data.append(item)
    return data
