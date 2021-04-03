# Урок 1, задача 1.
"""
Источник: https://5ka.ru/special_offers/

Задача организовать сбор данных,
необходимо иметь метод сохранения данных в .json файлы.

результат: Данные скачиваются с источника, при вызове метода/функции сохранения в файл скачанные данные сохраняются
 в Json файлы, для каждой категории товаров должен быть создан отдельный файл и содержать товары исключительно
 соответсвующие данной категории.

пример структуры данных для файла:
нейминг ключей можно делать отличным от примера

{
"name": "имя категории",
"code": "Код соответсвующий категории (используется в запросах)",
"products": [{PRODUCT}, {PRODUCT}........] # список словарей товаров соответсвующих данной категории
}
"""

from pathlib import Path
import time
import json
import requests


class Parse5ka:
    headers = {"User-Agent": "Mr.Who"}

    params = {
        "records_per_page": "100"
    }
    group_name = {
        "parent_group_name": ''
    }

    count = 0

    url_category = "https://5ka.ru/api/v2/categories/"
    response_category: requests.Response = requests.get(url_category, headers=headers)
    file_category = Path(__file__).parent.joinpath('5ka_category.json')
    file_category.write_text(response_category.text, encoding='utf-8')

    def __init__(self, start_url: str, save_path: Path):
        self.start_url = start_url
        self.save_path = save_path

    with open(file_category, encoding='utf-8') as cat_file:
        data_cat = json.load(cat_file)

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        while True:
            data_cat_choose_one = self.data_cat[self.count]
            self.params["categories"] = data_cat_choose_one.get('parent_group_code')
            self.group_name["parent_group_name"] = data_cat_choose_one.get('parent_group_name')
            print(self.params, self.group_name)

            response_site = requests.get(url, **kwargs, headers=self.headers, params=self.params)
            if response_site.status_code in (200, 301, 304):
                return response_site
            time.sleep(1)

    def run(self):
        for products_in_the_category in self._parse(self.start_url):
            product_path = self.save_path.joinpath(f"{self.params['categories']}.{self.group_name.get('parent_group_name')}.json")
            self._save(products_in_the_category, product_path)

    def _save(self, data, file_path):
        if file_path.exists():
            with open(file_path, encoding='utf-8') as json_file:
                data_exists = json.load(json_file)
                for product in data:
                    data_exists.append(product)
            file_path.write_text(json.dumps(data_exists, ensure_ascii=False), encoding='utf-8')

        if not file_path.exists():
            file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def _parse(self, url):
        while url:
            response = self._get_response(url)
            data: dict = response.json()
            url = data.get("next")
            if url is None:
                self.count += 1
                print(f"{self.count} из {len(self.data_cat)}")
            yield data.get("results", [])


def get_save_path(dir_name):
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path

if __name__ == "__main__":
    parser = Parse5ka("https://5ka.ru/api/v2/special_offers/", get_save_path("products_by_category"))
    while parser.count != len(parser.data_cat):
        parser.run()

