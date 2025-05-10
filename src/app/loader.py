import json
import logging
import re
import time
from datetime import UTC, datetime
from functools import cache

import requests
from requests import HTTPError, Session as HTTPSession
from requests.adapters import HTTPAdapter
from sqlalchemy import desc, select
from urllib3.util.retry import Retry

from app.config.settings import settings
from app.db import Session
from app.db.models import Category, Feature, Product, ProductCategory
from app.schemas.categories import CategorySchema
from app.schemas.product import ProductCharacteristic, ProductSchema

log = logging.getLogger(__name__)


# A retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False,
)

# Attach this to a session
adapter = HTTPAdapter(max_retries=retry_strategy)


def login():
    s = HTTPSession()
    s.mount("https://", adapter)

    log.info("logging in")
    rs = s.get("https://arbuz.kz")
    platform_conf_raw = re.search(r"window\.platformConfiguration = (.*)?;", rs.text).groups()[0]
    platform_conf = json.loads(platform_conf_raw)
    rs = s.post(
        settings.api("auth/token"),
        data={
            "consumer": platform_conf["consumer"]["desktop"]["name"],
            "key": platform_conf["consumer"]["desktop"]["key"],
        },
    )
    rs.raise_for_status()
    return s


@cache
def get_base_categories() -> dict[int, CategorySchema]:
    rs = requests.get("https://arbuz.kz/")
    catalog_tree_raw = re.search(r"window\.siteCatalogTree = Object\.values\((.*)?\);", rs.text).groups()[0]
    catalog_tree = json.loads(catalog_tree_raw)  # {"0": {...}, "1": {...}}
    cats = {}
    for category in catalog_tree.values():
        cat = CategorySchema(**category)
        cats[cat.id] = cat
        if category["children"]:
            for child in category["children"].values():
                child_cat = CategorySchema(parent_id=cat.id, **child)
                cats[child_cat.id] = child_cat
    return cats


def get_category_info(s: HTTPSession, cat: CategorySchema) -> tuple[int, list[CategorySchema]]:
    log.info("getting info for %s ", cat)
    rs = s.get(settings.api(f"shop/catalog/{cat.id}"), params={"limit": 0, "page": 1})
    rs.raise_for_status()
    data = rs.json()
    catalogs = [CategorySchema(**c) for c in data["data"]["catalogs"]["data"]]
    product_cnt = data["data"]["products"]["count"]
    return product_cnt, catalogs


def get_catalog_products(s: HTTPSession, cat: Category, limit: int = 40, page: int = 1) -> list[ProductSchema]:
    log.info("getting %r products, page %d of size %d", cat.name, page, limit)
    rs = s.get(settings.api(f"shop/catalog/{cat.id}"), params={"limit": limit, "page": page, "sort[mock]": ""})
    rs.raise_for_status()
    data = rs.json()
    pss = []
    for i, p in enumerate(data["data"]["products"]["data"]):
        sort_pos = i + 1 + ((page - 1) * limit)
        ps = ProductSchema(sort_pos=sort_pos, **p)
        ps.catalog_id = cat.id  # overwrite to the catalog that we found the product in
        pss.append(ps)
    return pss


def import_category(s: Session, cs: CategorySchema) -> Category:
    parent_cat = None
    if cs.parent_id:
        parent_cs = get_base_categories()[cs.parent_id]
        parent_cat = import_category(s, parent_cs)

    cat = s.scalar(select(Category).where(Category.id == cs.id))
    if not cat:
        log.info("creating %s", cs)
        cat = Category(id=cs.id, name=cs.name, uri=cs.uri, parent=parent_cat)
    else:
        log.info("updating %s", cs)
        cat.name = cs.name
        cat.uri = cs.uri
        cat.parent = parent_cat

    s.add(cat)
    return cat


def import_feature(s: Session, pc: ProductCharacteristic) -> Feature:
    feat = s.scalar(select(Feature).where(Feature.id == pc.id))
    if not feat:
        feat = Feature(id=pc.id, name=pc.name)
    else:
        feat.name = pc.name
    s.add(feat)
    return feat


def import_product(s: Session, ps: ProductSchema) -> Product:
    feats = [import_feature(s, pc) for pc in ps.characteristics]
    p: Product = s.scalar(select(Product).where(Product.id == ps.id))

    if not p:
        log.info("creating %s", ps)
        p = Product(
            id=ps.id,
            name=ps.name,
            producer_country=ps.producer_country,
            brand_name=ps.brand_name,
            description=ps.description,
            image_url=str(ps.image),
            measure=ps.measure,
            is_weighted=ps.is_weighted,
            weight_avg=ps.weight_avg,
            weight_min=ps.weight_min,
            weight_max=ps.weight_max,
            weight=ps.weight,
            piece_weight_min=ps.piece_weight_min,
            piece_weight_max=ps.piece_weight_max,
            sell_by_piece=ps.sell_by_piece,
            quantity_min_step=ps.quantity_min_step,
            price_actual=ps.price_actual,
            price_special=ps.price_special,
            price_previous=ps.price_previous,
            is_available=ps.is_available,
            is_local=ps.is_local,
            nutrition_fats=ps.nutrition.fats if ps.nutrition else None,
            nutrition_protein=ps.nutrition.protein if ps.nutrition else None,
            nutrition_kcal=ps.nutrition.kcal if ps.nutrition else None,
            nutrition_carbs=ps.nutrition.carbs if ps.nutrition else None,
            ingredients=ps.ingredients,
            storage_conditions=ps.storage_conditions,
            features=feats,
            information=ps.information,
            rating_value=ps.rating.value if ps.rating else None,
            rating_reviews=ps.rating.reviews if ps.rating else None,
        )
    else:
        log.debug("updating %s", ps)
        p.features.extend([feat for feat in feats if feat not in p.features])

        p.name = ps.name
        p.producer_country = ps.producer_country
        p.brand_name = ps.brand_name
        p.description = ps.description
        p.image_url = str(ps.image)
        p.measure = ps.measure
        p.is_weighted = ps.is_weighted
        p.weight_avg = ps.weight_avg
        p.weight_min = ps.weight_min
        p.weight_max = ps.weight_max
        p.weight = ps.weight
        p.piece_weight_min = ps.piece_weight_min
        p.piece_weight_max = ps.piece_weight_max
        p.sell_by_piece = ps.sell_by_piece
        p.quantity_min_step = ps.quantity_min_step
        p.price_actual = ps.price_actual
        p.price_special = ps.price_special
        p.price_previous = ps.price_previous
        p.is_available = ps.is_available
        p.is_local = ps.is_local
        p.nutrition_fats = ps.nutrition.fats if ps.nutrition else None
        p.nutrition_protein = ps.nutrition.protein if ps.nutrition else None
        p.nutrition_kcal = ps.nutrition.kcal if ps.nutrition else None
        p.nutrition_carbs = ps.nutrition.carbs if ps.nutrition else None
        p.ingredients = ps.ingredients
        p.storage_conditions = ps.storage_conditions
        p.information = ps.information
        p.rating_value = ps.rating.value if ps.rating else None
        p.rating_reviews = ps.rating.reviews if ps.rating else None
    s.add(p)

    # add category & position in it
    p_cat = s.scalar(
        select(ProductCategory).where(
            (ProductCategory.category_id == ps.catalog_id) & (ProductCategory.product_id == ps.id)
        )
    )
    if not p_cat:
        cat = s.scalar(select(Category).where(Category.id == ps.catalog_id))
        p_cat = ProductCategory(product=p, category=cat)
    p_cat.sort_pos = ps.sort_pos
    s.add(p_cat)
    return p


def import_products(pss: list[ProductSchema]) -> list[Product]:
    products = []
    with Session() as s, s.begin():
        for ps in pss:
            p = import_product(s, ps)
            products.append(p)
    return products


def import_category_products(client: HTTPSession, cat: Category, s: Session):
    log.info("importing products of %r", cat.name)
    page = 1
    while True:
        try:
            products = get_catalog_products(client, cat, limit=40, page=page)
        except HTTPError as e:
            if e.response.status_code == 404:
                log.info("no products found for %r", cat.name)
                return
            else:
                raise

        import_products(products)
        if len(products) < 40:
            log.info("products imported for %r", cat.name)
            break
        page += 1
        time.sleep(4)

    cat.updated_at = datetime.now(UTC)
    s.add(cat)
    s.commit()


def load_category(cs: CategorySchema, client: HTTPSession, s: Session):
    import_category(s, cs)
    time.sleep(2)

    # look deeper into the category
    try:
        cnt, sub_css = get_category_info(client, cs)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            log.info("category not found: %s", cs)
            return
        else:
            raise
    if sub_css:
        log.info("importing %d subcategories for %s", len(sub_css), cs.name)
    for sub_cs in sub_css:
        load_category(sub_cs, client, s)
    s.commit()


def load_categories() -> None:
    client = login()
    base_css = list(get_base_categories().values())

    with Session() as s:
        for base_cs in base_css:
            load_category(base_cs, client, s)


def load_products() -> None:
    client = login()
    with Session() as s:
        cats: list[Category] = s.scalars(select(Category).order_by(desc(Category.updated_at))).all()
        log.info("%d categories selected for an update", len(cats))
        for cat in cats:
            time.sleep(2)
            import_category_products(client, cat, s)
