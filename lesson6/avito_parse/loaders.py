# import re
from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Join
# from urllib.parse import urljoin


# def hh_full_url(user):
#     return urljoin("https://spb.hh.ru/", user)


def clear_item(any_item):
    item_c = any_item.replace('\xa0', '', 100)
    return item_c


def get_parameters_of_flat(item: str) -> dict:
    selector = Selector(text=item)
    name = selector.xpath("//span[contains(@class, 'item-params-label')]/text()").extract_first()
    value = selector.xpath("//text()").extract()[-1]
    data = {name: value}
    return data


class AvitoLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_in = MapCompose(clear_item)
    title_out = TakeFirst()
    price_out = TakeFirst()
    adress_of_flat_out = TakeFirst()
    description_in = MapCompose(clear_item)
    description_out = Join()
    parameters_of_flat_in = MapCompose(get_parameters_of_flat)
    author_url_out = TakeFirst()