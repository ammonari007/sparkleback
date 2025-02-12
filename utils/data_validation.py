def valid_data(item):
    if not item:
        return None
    elif isinstance(item, (str, tuple)):
        return valid_list(item)
    elif isinstance(item, dict):
        return valid_dict(item)
    elif isinstance(item, str):
        return item if len(item) else None
    else:
        return item


def valid_list(item):
    if not item and not len(item):
        return None
    cleaned = [i for i in item if valid_data(i)]
    return cleaned if len(cleaned) else None


def valid_dict(item):
    if not item:
        return None
    cleaned = {k: v for k, v in metadata.items() if valid_data(v)}
    return cleaned if len(list(cleaned.keys())) else None
