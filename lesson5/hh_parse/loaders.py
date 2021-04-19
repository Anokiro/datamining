# import re
# from scrapy import Selector
from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Join
from urllib.parse import urljoin


def clear_wages(wages):
    item_wa = wages.replace('\xa0', '', 10)
    return item_wa


def hh_full_url(user):
    return urljoin("https://spb.hh.ru/", user)


def clear_item(any_item):
    item_c = any_item.replace('\xa0', '', 10)
    return item_c


class HhruLoader(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    title_of_vacancy_out = TakeFirst()
    needs_to_skills_in = MapCompose(clear_item)
    needs_to_skills_out = Join(', ')
    description_of_vacancy_in = Join()
    description_of_vacancy_out = TakeFirst()
    wages_of_vacancy_in = MapCompose(clear_wages)
    wages_of_vacancy_out = Join()
    author_url_in = MapCompose(hh_full_url)
    author_url_out = TakeFirst()
    company_name_in = MapCompose(clear_item)
    company_name_out = Join()
# -------------------------------------


class HhruLoaderCompany(ItemLoader):
    default_item_class = dict
    url_out = TakeFirst()
    company_name_in = MapCompose(clear_item)
    company_name_out = Join()
    site_link_out = TakeFirst()
    field_of_activity_out = Join(', ')
    descr_company_in = MapCompose(clear_item)
    descr_company_out = Join()
    all_vacancy_in_company_link_out = TakeFirst()