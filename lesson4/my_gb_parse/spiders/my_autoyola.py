# Урок 4, задача 1.
"""
Источник https://auto.youla.ru/
Обойти все марки авто и зайти на странички объявлений.
Собрать след стуркутру и сохранить в БД Монго:

+ Название объявления

+ Список фото объявления (ссылки)
Список характеристик

+ Описание объявления

ссылка на автора объявления

дополнительно попробуйте вытащить телефон
"""
import base64
import codecs
import re
from urllib.parse import unquote

import pymongo
# 1. pip install scrapy
# 2. затем сделать запуск проекта:
#  scrapy startproject my_gb_parse .  (точку(путь)ставить обязательно)
# 3. создать паука:
#  scrapy genspider my_autoyola auto.youla.ru
import scrapy


class MyAutoyolaSpider(scrapy.Spider):
    name = 'my_autoyola'
    allowed_domains = ['auto.youla.ru']
    start_urls = ["https://auto.youla.ru/"]

    # TODO: в дальнейшем в данном пауке использовать _xpath_selectors
    _css_selectors = {
        "brands": "div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "car": "#serp article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_client = pymongo.MongoClient()


    def _get_follow(self, response, selector_css, callback, **kwargs):
        for link_selector in response.css(selector_css):
            yield response.follow(link_selector.attrib.get("href"), callback=callback)

    def parse(self, response, **kwargs):
        print(1)
        yield from self._get_follow(response, self._css_selectors["brands"], self.brand_parse)

    def brand_parse(self, response):
        yield from self._get_follow(response, self._css_selectors["pagination"], self.brand_parse)
        yield from self._get_follow(response, self._css_selectors["car"], self.car_parse)

    def car_parse(self, response):
        # TODO: использовать более легкие селекторы
        full_foto_list1 = lambda response: MyAutoyolaSpider.get_full_photo_list(response)
        full_foto_list2 = full_foto_list1(response)

        author1 = lambda resp: MyAutoyolaSpider.get_author_id(response)
        author2 = author1(response)

        data = {
            "title": response.css(".AdvertCard_advertTitle__1S1Ak::text").extract_first(),
            "url": response.url,
            "full_foto_list": full_foto_list2,
            # "photo_list": response.css(".PhotoGallery_photoWrapper__3m7yM figure.PhotoGallery_photo__36e_r img::attr(src)").getall(),
            "characteristics_list": self.get_character(response),
            "description": response.css(
                ".AdvertCard_descriptionInner__KnuRi::text"
            ).extract_first(),
            "equipment_list": self.get_equip_items(response),
            "author": author2,
            "phone": self.get_author_phone(response)
        }
        self._save(data)
        yield data

    # TODO: паук не должен обрабатывать и сохранять данные, в дальнейшем сделать через pipeline
    def _save(self, data):
        self.db_client["my_gb_parse_lesson4"][self.name].insert_one(data)

    def get_equip_items(self, response):
        items_list = []
        advert_equipment_items = response.css(".AdvertEquipment_equipmentItem__Jk5c4::text").extract()
        for one_advert_equipment_item in advert_equipment_items:
            if len(one_advert_equipment_item) > 2 and one_advert_equipment_item.islower() != True:
                items_list.append(one_advert_equipment_item)
        return items_list

    def get_character(self, response):
        characterictics_list = []
        characterictics_dict = {}
        for name, character in zip(response.css(".AdvertSpecs_label__2JHnS"), response.css(".AdvertSpecs_data__xK2Qx")):
            name_in_response = name.css("::text").extract_first()
            character_in_response = character.css("::text").extract_first()
            characterictics_dict[name_in_response] = character_in_response
        characterictics_list.append(characterictics_dict)
        return characterictics_list

    @staticmethod
    def get_full_photo_list(response):
        marker = "window.transitState = decodeURIComponent"
        for script in response.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    url_with_unquote = unquote(str(script.css("::text").extract_first()))
                    re_pattern = re.compile("https://static.am/automobile_m3/document/xl/[a-zA-Z|\d]+/[a-zA-Z|\d]+/[a-zA-Z&\d]+.jpg")
                    result = re.findall(re_pattern, url_with_unquote)
                    return (
                        result
                        if result
                        else None
                    )
            except TypeError:
                pass

    @staticmethod
    def get_author_id(response):
        marker = "window.transitState = decodeURIComponent"
        for script in response.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    re_pattern = re.compile(r"youlaId%22%2C%22([a-zA-Z|\d]+)%22%2C%22avatar")
                    result = re.findall(re_pattern, script.css("::text").extract_first())
                    return (
                        response.urljoin(f"/user/{result[0]}").replace("auto.", "", 1)
                        if result
                        else None
                    )
            except TypeError:
                pass

    @staticmethod
    def get_author_phone(response):
        marker = "window.transitState = decodeURIComponent"
        for script in response.css("script"):
            try:
                if marker in script.css("::text").extract_first():
                    url_with_unquote = unquote(str(script.css("::text").extract_first()))
                    re_pattern = re.compile("([a-zA-Z&\d]+)w==")
                    result = re.findall(re_pattern, url_with_unquote)
                    if len(result) > 0:
                        result_final = result[0] + 'w=='
                        step1 = str(result_final)
                        bytes1 = step1.encode("UTF-8")

                        decode1 = base64.b64decode(bytes1)
                        step2 = decode1.decode("UTF-8")
                        step3 = codecs.encode(step2, 'UTF-8')
                        step4 = base64.b64decode(step3)
                        step5 = step4.decode("UTF-8")
                        return (
                            step5
                            if step5
                            else None
                        )
            except TypeError:
                pass