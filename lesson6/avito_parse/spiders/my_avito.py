# Урок 6, задача 1.
"""
Источник https://www.avito.ru/krasnodar/kvartiry/prodam
задача обойти пагинацию и подразделы квартир в продаже.
Собрать данные:
URL
Title
Цена
Адрес (если доступен)
Параметры квартиры (блок под фото)
Ссылку на автора

Дополнительно но не обязательно вытащить телефон автора
"""
import scrapy
from lesson6.avito_parse.loaders import AvitoLoader

class MyAvitoSpider(scrapy.Spider):
    name = 'my_avito'
    allowed_domains = ['www.avito.ru']
    start_urls = ['https://www.avito.ru/krasnodar/kvartiry/prodam-ASgBAgICAUSSA8YQ?cd=1']

    _xpath_selectors = {
        "pagination": "//div[contains(@class, 'js-pages pagination-pagination-2j5na')]"
                      "//div[contains(@class, 'pagination-pages clearfix')]/a/@href",
        "advertisement": "//div[contains(@class, 'iva-item-root-G3n7v')]"
                         "//a[contains(@class, 'iva-item-sliderLink-2hFV_')]/@href"
    }

    _xpath_data_query = {

        "title": "//div[contains(@class, 'item-view-title-info')]"
                 "//h1[contains(@class, 'title-info-title')]/span/text()",
        "price": "//div[contains(@class, 'item-price-wrapper')]//span[contains(@class, 'js-item-price')]/@content",
        "adress_of_flat": "//div[contains(@class, 'item-map js-item-map')]"
                          "//span[contains(@class, 'item-address__string')]/text()",
        "description": "//div[contains(@class, 'item-description')]"
                       "/div[@itemprop='description']//text()",
        "parameters_of_flat": "//div[contains(@class, 'item-view-block')]/div[contains(@class, 'item-params')]/ul/li",
        "author_url": "//div[contains(@class, 'item-view-seller-info')]"
                      "//div[contains(@class, 'seller-info-prop js-seller-info-prop_seller-name')]"
                      "//div[@data-marker='seller-info/name']/a/@href",
    }

    def _get_follow_xpath(self, response, xpath, callback):
        for url in response.xpath(xpath):
            yield response.follow(url, callback=callback)

    def parse(self, response, **kwargs):
        callbacks = {"pagination": self.parse, "advertisement": self.advertisement_parse}
        for key, xpath in self._xpath_selectors.items():
            yield from self._get_follow_xpath(response, xpath, callbacks[key])

    def advertisement_parse(self, response):
        loader = AvitoLoader(response=response)
        loader.add_value("url", response.url)
        for key, xpath in self._xpath_data_query.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()
