import asyncio
import decimal
import random
import time
from typing import List, Union

from aiodataloader import DataLoader
from ariadne import (
    ObjectType,
    SchemaBindable,
    load_schema_from_path,
    make_executable_schema,
)
from ariadne.asgi import GraphQL
from faker import Faker

from mocking import MockResolverSetter, FactoryMap


class ProductLoader(DataLoader):
    async def batch_load_fn(self, keys):
        print("batch_load start", keys)
        await asyncio.sleep(1)
        # time.sleep(1)
        print("batch_load_end")
        return map(lambda id: {"name": fake.company(), "id": id}, keys)


product_loader = ProductLoader()


fake = Faker()


type_defs = load_schema_from_path("schema.graphql")


factory_map = FactoryMap()


@factory_map.type("Money")
def fake_money(value):
    if isinstance(value, dict):
        return value
    if not isinstance(value, decimal.Decimal):
        value = decimal.Decimal(random.random() * 1000).quantize(decimal.Decimal(".01"))
    return {"currency": "USD", "amount": value}


@factory_map.type("TaxedMoney")
def fake_taxed_money(value):
    if isinstance(value, dict):
        return value
    return {"net": fake_money(value), "gross": fake_money(value), "tax": decimal.Decimal(0)}


@factory_map.type("TaxedMoneyRange")
def fake_taxed_money_range(value):
    start, stop = sorted([fake_taxed_money(value), fake_taxed_money(value)], key=lambda v: v['gross']['amount'])
    return {"start": start, "stop": stop}


@factory_map.type("Image")
def fake_image(_, size="200"):
    return {"url": f"https://placekitten.com/{size}/{size}", "alt": fake.sentence()}


@factory_map.type("PageInfo")
def fake_page_info(_):
    return {"hasNextPage": False, "hasPreviousPage": False}


@factory_map.type("ProductCountableConnection")
def fake_product_countable_connection(_, first=10, last=None):
    return {"edges": range(last or first), "totalCount": last or first}


@factory_map.type("Product")
def fake_product(_, id=None):
    return product_loader.load(id or fake.pystr())


@factory_map.type("VAT")
def fake_vat(_):
    return {"reducedRates": range(10)}


product = ObjectType("Product")


@product.field("name")
async def resolve_product_name(product, info):
    print("resolve_product_name start", product)
    await asyncio.sleep(1)
    # time.sleep(1)
    print("resolve_product_name end", product)
    return product["name"]


schema = make_executable_schema(type_defs, [product, MockResolverSetter(factory_map)])

app = GraphQL(schema, debug=True)
