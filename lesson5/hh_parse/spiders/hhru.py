# Урок 5, задача 1.
"""
Источник https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113
вакансии удаленной работы.

Задача: Обойти с точки входа все вакансии и собрать след данные:
1. название вакансии
2. оклад (строкой от до или просто сумма)
3. Описание вакансии
4. ключевые навыки - в виде списка названий
5. ссылка на автора вакансии

Перейти на страницу автора вакансии,
собрать данные:
1. Название
2. сайт ссылка (если есть)
3. сферы деятельности (списком)
4. Описание

Обойти и собрать все вакансии данного автора.
"""
import scrapy

from lesson5.hh_parse.loaders import HhruLoader
from lesson5.hh_parse.loaders import HhruLoaderCompany

class HhruSpider(scrapy.Spider):

    name = 'hhru'
    allowed_domains = ['spb.hh.ru']
    start_urls = ['https://spb.hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    _xpath_data_query = {

        "title_of_vacancy": "//h1[@data-qa='vacancy-title']/text()",
        "wages_of_vacancy": "//p[@class='vacancy-salary']/span/text()",
        "description_of_vacancy": "//div[@data-qa='vacancy-description']//text()",
        "needs_to_skills": "//div[@class='bloko-tag-list']//div[contains(@data-qa, 'skills-element')]/"
                           "span[@data-qa='bloko-tag__text']/text()",
        "author_url": "//div[contains(@class, 'vacancy-company__details')]/a[@data-qa='vacancy-company-name']/@href",
    }

    _xpath_selectors = {
        "pagination": "//span[contains(@class, 'bloko-button-group')]//span/a/@href",
        "vacancy": "//div[contains(@data-qa, 'vacancy-serp__vacancy')]//"
                   "a[@data-qa='vacancy-serp__vacancy-title']/@href",
        "company": "//div[contains(@class, 'vacancy-serp-item')]"
                   "//div[contains(@class, 'vacancy-serp-item__meta-info-company')]/a/@href"
    }

    def _get_follow_xpath(self, response, selector, callback):
        for url in response.xpath(selector):
            yield response.follow(url, callback=callback)

    def parse(self, response, **kwargs):
        callbacks = {"pagination": self.parse, "vacancy": self.vacancy_parse, "company": self.company_parse}
        for key, xpath in self._xpath_selectors.items():
            yield from self._get_follow_xpath(response, xpath, callbacks[key])

    def vacancy_parse(self, response):
        loader = HhruLoader(response=response)
        loader.add_value("url", response.url)
        comp_name = response.xpath(
            "//div[contains(@class, 'bloko-gap')]/div[contains(@class, 'bloko-columns-row')]"
            "//span[contains(@class, 'bloko-section-header-2_lite')]/text()").extract()
        loader.add_value("company_name", comp_name)
        for key, xpath in self._xpath_data_query.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()

    def company_parse(self, response):
        print(f'получил компанию {response}')
        data = {
            "company_name": "//div[contains(@class, 'company-header')]"
                                            "//span[contains(@class, 'company-header-title-name')]/text()",
            "site_link": "//div[contains(@class, 'employer-sidebar-content')]"
                                            "//a[contains(@class, 'g-user-content')]/@href",
            "field_of_activity": "//div[contains(@class, 'employer-sidebar-block')]/p/text()",
            "descr_company": "//div[contains(@class, 'bloko-gap_top')]"
                                                "//div[contains(@class, 'company-description')]"
                                                "//div[contains(@class, 'g-user-content')]/p/text()",
            "all_vacancy_in_company_link": "//div[contains(@class, 'employer-sidebar-block')]//a/@href",
            }

        loader = HhruLoaderCompany(response=response)
        loader.add_value("url", response.url)
        for key, xpath in data.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()