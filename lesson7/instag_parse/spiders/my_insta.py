# Урок 7, задача 1.
"""
Источник instgram
Задача авторизованным пользователем обойти список произвольных тегов,
Сохранить структуру Item, олицетворяющую сам Tag (только информация о теге)
Сохранить структуру данных поста, Включая обход пагинации. (каждый пост как отдельный item, словарь внутри node)

Все структуры должны иметь след вид:
date_parse (datetime) время когда произошло создание структуры
data - данные полученые от инстаграм
Скачать изображения всех постов и сохранить на диск
"""
# pip install python-dotenv
# pip install selenium
# pip install pillow (для того, чтобы Scrapy мог скачивать изображения)
import json
import datetime
from urllib.parse import urlencode
import scrapy
from ..items import InstagTag, InstagPost


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    _login_url = "https://www.instagram.com/accounts/login/ajax/"
    _tags_path = "/explore/tags/"
    api_url = "/graphql/query/"

    def __init__(self, login, password, tags, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.tags = tags

    def parse(self, response, **kwargs):
        try:
            js_data = self.get_js_data_extract(response)
            yield scrapy.FormRequest(
                self._login_url,
                method="POST",
                callback=self.parse,
                formdata={
                    "username": self.login,
                    "enc_password": self.password
                },
                headers={"X-CSRFToken": js_data["config"]["csrf_token"]},
            )
        except AttributeError:
            if response.json()["authenticated"]:
                for tag in self.tags:
                    yield response.follow(f"{self._tags_path}{tag}/", callback=self.tag_page_parse)

    def tag_page_parse(self, response):
        js_data = self.get_js_data_extract(response)
        yield InstagTag(date_parse=datetime.datetime.now(), data=self.get_structure_of_tag(js_data))
        yield response.follow(f"{self.api_url}?{urlencode(self.get_pagination(js_data))}", callback=self.api_parse)

    def api_parse(self, response):
        js_data_api = response.json()
        yield InstagPost(date_parse=datetime.datetime.now(),
                         data=self.get_structure_of_posts(js_data_api),
                         images=self.get_image_of_post(js_data_api))
        yield response.follow(f"{self.api_url}?{urlencode(self.get_pagination_for_api(js_data_api))}",
                              callback=self.api_parse)

    def get_structure_of_tag(self, js_data: dict):
        structure_dict = {}
        items_dict = {}
        for key, value in (js_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"]).items():
            if type(value) not in [type({}), type([])]:
                structure_dict[key] = value
            if type(value) in [type({}), type([])]:
                structure_dict[key] = 'there_are_dictionaries_here'
        structure_dict['data'] = items_dict
        return structure_dict

    def get_structure_of_posts(self, js_data_api: dict):
        structure_posts_dict = {}
        structure_posts_dict['edges'] = js_data_api["data"]["hashtag"]["edge_hashtag_to_media"]["edges"]
        structure_posts_dict['pagination'] = js_data_api["data"]["hashtag"]["edge_hashtag_to_media"]["page_info"][
            "end_cursor"]
        return structure_posts_dict

    def get_pagination(self, js_data: dict):
        dict_variables = {
            "tag_name": js_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"]["name"],
            "first": 66,
            "after": js_data["entry_data"]["TagPage"][0]["graphql"]["hashtag"]["edge_hashtag_to_media"]["page_info"][
                "end_cursor"]
        }
        query = {"query_hash": "9b498c08113f1e09617a1703c22b2f32", "variables": json.dumps(dict_variables)}
        return query

    def get_pagination_for_api(self, js_data_api: dict):
        dict_variables = {
            "tag_name": js_data_api['data']["hashtag"]["name"],
            "first": 66,
            "after": js_data_api["data"]["hashtag"]["edge_hashtag_to_media"]["page_info"][
                "end_cursor"]
        }
        query = {"query_hash": "9b498c08113f1e09617a1703c22b2f32", "variables": json.dumps(dict_variables)}
        return query

    def get_image_of_post(self, js_data_api):
        result = js_data_api['data']["hashtag"]["edge_hashtag_to_media"]["edges"]
        images_list = []
        for num_of_post in result:
            link_of_image = num_of_post["node"]["display_url"]
            images_list.append(link_of_image)
        return images_list

    def get_js_data_extract(self, response):
        script = response.xpath(
            "//script[contains(text(), 'window._sharedData = ')]/text()"
        ).extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])