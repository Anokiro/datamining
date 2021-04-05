# Урок 2, задача 1
"""
Источник https://magnit.ru/promo/?geo=moskva
Необходимо собрать структуры товаров по акции и сохранить их в MongoDB

пример структуры и типы обязательно хранить поля даты как объекты datetime
{
    "url": str,
    "promo_name": str,
    "product_name": str,
    "old_price": float,
    "new_price": float,
    "image_url": str,
    "date_from": "DATETIME",
    "date_to": "DATETIME",
}
"""
# pip install bs4  - для установки BeautufulSoup
# pip install lxml - для установки парсера
# pip install pymongo
import requests
from urllib.parse import urljoin
import bs4
import pymongo
import datetime


class MagnitParse:
    product_tag_glob = ''

    def __init__(self, start_url, db_client):
        self.start_url = start_url
        db = db_client["data_mining_lesson2_db"]
        self.collection = db["magnit"]

    def _get_response(self, url, *args, **kwargs):
        # TODO: Сделать Обработку ошибок и статусов
        return requests.get(url, *args, **kwargs)

    def _get_soup(self, url, *args, **kwargs):
        # TODO: Обработать ошибки
        return bs4.BeautifulSoup(self._get_response(url, *args, **kwargs).text, "lxml")

    def run(self):
        for product in self._parse(self.start_url):
            self._save(product)

    @property
    def _template(self):
        url1 = lambda tag: urljoin(self.start_url, tag.attrs.get("href", ""))
        url2 = url1(self.product_tag_glob)

        promo_name2 = lambda tag: tag.find("div", attrs={"class": "card-sale__header"})
        promo_name3 = promo_name2
        if promo_name2(self.product_tag_glob) is None:
            promo_name2 = 'название отсутствует'
        if promo_name3(self.product_tag_glob) is not None:
            promo_name1 = lambda tag: tag.find("div", attrs={"class": "card-sale__header"}).text
            promo_name2 = promo_name1(self.product_tag_glob)

        product_name2 = lambda tag: tag.find("div", attrs={"class": "card-sale__title"})
        product_name3 = product_name2
        if product_name2(self.product_tag_glob) is None:
            product_name2 = 'название отсутствует'
        if product_name3(self.product_tag_glob) is not None:
            product_name1 = lambda tag: tag.find("div", attrs={"class": "card-sale__title"}).text
            product_name2 = product_name1(self.product_tag_glob)

        old_price3 = lambda tag: tag.find("div", attrs={"class": "label__price_old"})
        old_price4 = old_price3
        if old_price3(self.product_tag_glob) is None:
            old_price3 = 0
        if old_price4(self.product_tag_glob) is not None:
            old_price1 = lambda tag: tag.find("div", attrs={"class": "label__price_old"}).text.split('\n')[1]
            old_price2 = lambda tag: tag.find("div", attrs={"class": "label__price_old"}).text.split('\n')[2]
            try:
                old_price3 = float(str(old_price1(self.product_tag_glob))+'.'+(str(old_price2(self.product_tag_glob))))
            except ValueError:
                old_price3 = 0

        new_price3 = lambda tag: tag.find("div", attrs={"class": "label__price_new"})
        new_price4 = new_price3
        if new_price3(self.product_tag_glob) is None or new_price3(self.product_tag_glob) is str:
            new_price3 = 0
        if new_price4(self.product_tag_glob) is not None:
            new_price1 = lambda tag: tag.find("div", attrs={"class": "label__price_new"}).text.split('\n')[1]
            new_price2 = lambda tag: tag.find("div", attrs={"class": "label__price_new"}).text.split('\n')[2]
            try:
                new_price3 = float(str(new_price1(self.product_tag_glob))+'.'+(str(new_price2(self.product_tag_glob))))
            except ValueError:
                new_price3 = 0

        image_url1 = lambda tag: tag.find("img", attrs={"class": "lazy"})['data-src']
        image_url2 = image_url1(self.product_tag_glob)

        date_from1 = lambda tag: tag.find("div", attrs={"class": "card-sale__date"}).text.split('\n')[1]
        date_from2 = date_from1(self.product_tag_glob)
        date_to1 = lambda tag: tag.find("div", attrs={"class": "card-sale__date"}).text.split('\n')[2]
        date_to2 = date_to1(self.product_tag_glob)
        dict_to_replace = {
            "января": "01",
            "февраля": "02",
            "марта": '03',
            "апреля": '04',
            "мая": "05",
            "июня": "06",
            "июля": "07",
            "августа": "08",
            "сентября": "09",
            "октября": "10",
            "ноября": "11",
            "декабря": "12"
        }
        for key in dict_to_replace.keys():
            date_from2 = date_from2.replace(key, str(dict_to_replace[key]))
            date_to2 = date_to2.replace(key, str(dict_to_replace[key]))

        try:
            date_from3 = f"{datetime.datetime.now().year}-{date_from2.split(' ')[2]}-{date_from2.split(' ')[1]}"
            date_time_from_obj = datetime.datetime.strptime(date_from3, '%Y-%m-%d')
            date_to3 = f"{datetime.datetime.now().year}-{date_to2.split(' ')[2]}-{date_to2.split(' ')[1]}"
            date_time_to_obj = datetime.datetime.strptime(date_to3, '%Y-%m-%d')
        except IndexError:
            date_from1 = lambda tag: tag.find("div", attrs={"class": "card-sale__date"}).text.split('\n')[1]
            date_from2 = date_from1(self.product_tag_glob)
            date_to1 = lambda tag: tag.find("div", attrs={"class": "card-sale__date"}).text.split('\n')[1]
            date_to2 = date_to1(self.product_tag_glob)
            for key in dict_to_replace.keys():
                date_from2 = date_from2.replace(key, str(dict_to_replace[key]))
                date_to2 = date_to2.replace(key, str(dict_to_replace[key]))

            date_from3 = f"{datetime.datetime.now().year}-{date_from2.split(' ')[2]}-{date_from2.split(' ')[1]}"
            date_time_from_obj = datetime.datetime.strptime(date_from3, '%Y-%m-%d')
            date_to3 = f"{datetime.datetime.now().year}-{date_to2.split(' ')[2]}-{date_to2.split(' ')[1]}"
            date_time_to_obj = datetime.datetime.strptime(date_to3, '%Y-%m-%d')

        return {
            "url": url2,
            "promo_name": promo_name2,
            "product_name": product_name2,
            "old_price": old_price3,
            "new_price": new_price3,
            "image_url": image_url2,
            "date_from": date_time_from_obj,
            "date_to": date_time_to_obj
        }

    def _parse(self, url):
        soup = self._get_soup(url)
        catalog_main = soup.find("div", attrs={"class": "сatalogue__main"})
        product_tags = catalog_main.find_all("a", recursive=False)
        for product_tag in product_tags:
            self.product_tag_glob = product_tag
            product = {}
            for key, funk in self._template.items():
                product[key] = funk
            yield product

    def _save(self, data):
        self.collection.insert_one(data)


if __name__ == "__main__":
    url = "https://magnit.ru/promo/"
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParse(url, db_client)
    parser.run()
