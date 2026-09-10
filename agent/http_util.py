import requests

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "am-wire-morning-intelligence/0.1",
}


def get_json(url, params=None, extra_headers=None, timeout=20):
    headers = dict(HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    response = requests.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def to_float(value):
    if value is None or value == "":
        return None
    return float(value)
