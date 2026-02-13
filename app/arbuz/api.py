import json
import logging
import re

import httpx
from httpx_retries import Retry, RetryTransport

from app.config import settings

log = logging.getLogger(__name__)


_retry_policy = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)


_client = httpx.Client(
    base_url=str(settings.arbuz_base_url),
    transport=RetryTransport(retry=_retry_policy),
    timeout=30,
)


def login():
    rs = _client.get("/")
    platform_conf_raw_re = re.search(r"window\.platformConfiguration = (.*)?;", rs.text)
    if not platform_conf_raw_re:
        raise ValueError("Failed to retrieve platform configuration")
    platform_conf_raw = platform_conf_raw_re.groups()[0]
    platform_conf = json.loads(platform_conf_raw)
    rs = _client.post(
        "/api/v1/auth/token",
        data={
            "consumer": platform_conf["consumer"]["desktop"]["name"],
            "key": platform_conf["consumer"]["desktop"]["key"],
        },
    )
    rs.raise_for_status()
    log.info("logged in")


def get_catalog_tree_json():
    rs = _client.get("/")
    catalog_tree_raw_re = re.search(r"window\.siteCatalogTree = Object\.values\((.*)?\);", rs.text)
    if not catalog_tree_raw_re:
        raise ValueError("Failed to retrieve catalog tree")
    catalog_tree_raw = catalog_tree_raw_re.groups()[0]
    catalog_tree = json.loads(catalog_tree_raw)
    return catalog_tree


def get_category_info_json(cat_id: int):
    rs = _client.get(f"/api/v1/shop/catalog/{cat_id}", params={"limit": 0, "page": 1})
    rs.raise_for_status()
    return rs.json()


def get_catalog_products_json(cat_id: int, limit: int = 40, page: int = 1):
    rs = _client.get(f"/api/v1/shop/catalog/{cat_id}", params={"limit": limit, "page": page, "sort[mock]": ""})
    rs.raise_for_status()
    return rs.json()


login()
