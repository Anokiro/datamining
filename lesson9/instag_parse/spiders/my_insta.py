"""
Источник instgram
Задача:
На вход программе подается 2 имени пользователя.
Задача программы найти самую короткую цепочку рукопожатий между этими пользователями,
рукопожатием считается только взаимоподписка пользователей.
"""
# pip install python-dotenv
# pip install selenium
# pip install pillow (для того, чтобы Scrapy мог скачивать изображения)
import json
# import datetime
from urllib.parse import urlencode
import scrapy
# from scrapy import Request
# from ..items import InstagTag, InstagPost


class InstagramSpider(scrapy.Spider):
    name = "instagram"
    allowed_domains = ["www.instagram.com"]
    start_urls = ["https://www.instagram.com/"]
    _login_url = "https://www.instagram.com/accounts/login/ajax/"
    api_url = "/graphql/query/"

    #Подписчики
    followers_name_dict = {}
    # Подписки
    following_name_dict = {}

    counter_filtered = 0

    one_friend_next_parse_counter = 0
    non_unique_counter = 0
    one_friend_next_parse_counter2 = 0

    followers_name_friends_dict = {}

    follower_one_dict = {}
    follower_one_dict_step2 = {}

    flag_continuation = 0

    count_friends = {}
    count_friends_step2 = {}

    # query_hash = {
    #     'following': '3dec7e2c57367ef3da3d987d89f9dbc8',
    #     'followers': '5aefa9893005572d237da5068082d8d5'
    # }

    def __init__(self, login, password, accounts_list, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login = login
        self.password = password
        self.accounts_list = accounts_list
        self.user1 = accounts_list[0]
        self.user2 = accounts_list[1]

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
                for number, user in enumerate(self.accounts_list):
                    cookies = response.headers.getlist('Set-Cookie')
                    print(cookies)
                    yield response.follow(f"https://www.instagram.com/{user}", callback=self.user_page_parse,
                                          meta={
                                              # 'dont_merge_cookies': True,
                                              # 'cookiejar': number,
                                                     "side": str(number + 1),
                                              # "number_user": str(number + 1),
                                                "user_name": user})

    def user_page_parse(self, response):
        js_data = self.get_js_data_extract(response)
        user_name = response.meta["user_name"]
        side = response.meta["side"]
        # print(response.meta['cookiejar'])

        is_business_account = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['is_business_account']
        is_professional_account = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['is_professional_account']
        is_private_account = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['is_private']
        if is_business_account is True and is_professional_account is True and is_private_account is True:
            self.counter_filtered += 1
        if is_business_account is False and is_professional_account is False and is_private_account is False:
            yield response.follow(f"{self.api_url}?{urlencode(self.get_pagination(js_data))}",
                              callback=self.step_one_followers_parse,
                              meta={
                                  # 'cookiejar': response.meta['cookiejar'],
                                  # 'dont_merge_cookies': True,
                                    'id': str(js_data['entry_data']['ProfilePage'][0]['graphql']['user']['id']),
                                    "user_name": user_name, "side": side})

    def step_one_followers_parse(self, response):
        if response.status not in [200, 301, 304]:
            print(f"{response.meta['user_name']} не имеет статус код 200, 301 или 304 !!! ")
        if response.status in [200, 301, 304]:
            id_user_response = response.meta['id']
            name_user_response = response.meta['user_name']
            side = response.meta["side"]
            if name_user_response not in self.followers_name_dict or name_user_response in self.accounts_list:

                # ----------------------------------------------------------->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
                if name_user_response in self.accounts_list:

                    if name_user_response not in self.followers_name_dict:
                        self.followers_name_dict[name_user_response] = set()

                    js_data_api = response.json()
                    check_next = js_data_api["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]
                    self.count_friends[name_user_response] = js_data_api['data']["user"]["edge_followed_by"]["count"]
                    sum_count = -1
                    if len(self.count_friends) > 1:
                        sum1 = self.count_friends[self.user1]
                        sum2 = self.count_friends[self.user2]
                        sum_count = int(sum1) + int(sum2)

                    result = js_data_api['data']["user"]["edge_followed_by"]["edges"]
                    for item in result:
                        name_of_user = item["node"]["username"]
                        self.followers_name_dict[name_user_response].add(str(name_of_user))

                    if check_next is True:
                        yield response.follow(
                            f"{self.api_url}?{urlencode(self.get_pagination_for_api(js_data_api, id_user_response))}",
                            callback=self.step_one_followers_parse, meta={
                                                                            # 'cookiejar': response.meta['cookiejar'],
                                                                            # 'dont_merge_cookies': True,
                                                                          "id": str(id_user_response),
                                                                          "user_name": name_user_response,
                                                                          "side": side})

                    if check_next is False:
                        try:
                            first = len(self.followers_name_dict[self.user1])
                            second = len(self.followers_name_dict[self.user2])
                            if (int(first) + int(second)) == sum_count:
                                non_unique = self.followers_name_dict[self.user1].intersection(self.followers_name_dict[self.user2])
                                if non_unique != set():
                                    print(f"Следующие пользователи {non_unique} есть одновременно в подписчиках у {self.user1} и {self.user2}")
                                    self.non_unique_counter = len(non_unique)
                                    for num, user_in_followers in enumerate(non_unique):
                                        yield response.follow(f"https://www.instagram.com/{user_in_followers}",
                                                              callback=self.one_friend_parse,
                                                              meta={
                                                                  # 'cookiejar': response.meta['cookiejar'],
                                                                  #   'dont_merge_cookies': True,
                                                                  "user_name": user_in_followers,
                                                                    })
                                if non_unique == set():
                                    print("Ищу дальше...")
                                    local_list_nu = [self.followers_name_dict[self.user1], self.followers_name_dict[self.user2]]
                                    for number_nu, set_nu in enumerate(local_list_nu):
                                        for numb, one_user_nu in enumerate(set_nu):
                                            yield response.follow(f"https://www.instagram.com/{one_user_nu}",
                                                                  callback=self.user_page_parse,
                                                                  meta={
                                                                      # 'cookiejar': numb,
                                                                      #   'dont_merge_cookies': True,
                                                                        "user_name": one_user_nu,
                                                                        "side": (number_nu + 1)})
                        except KeyError:
                            pass
                # -----------------------------------------------------------<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                if name_user_response not in self.accounts_list:
                    if self.flag_continuation == 0: # проработать еще данную часть.
                        if str(side) not in self.followers_name_friends_dict:
                            self.followers_name_friends_dict[str(side)] = {}
                        if name_user_response not in self.followers_name_friends_dict[str(side)]:
                            self.followers_name_friends_dict[str(side)][name_user_response] = set()

                        print(name_user_response)
                        js_data_api_f = response.json()
                        check_next_f = js_data_api_f["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]

                        if str(side) not in self.count_friends_step2:
                            self.count_friends_step2[str(side)] = {}
                        if name_user_response not in self.count_friends_step2[str(side)]:
                            count_friends = js_data_api_f['data']["user"]["edge_followed_by"]["count"]
                            if type(count_friends) is not int:
                                self.count_friends_step2[str(side)][name_user_response] = 0
                            else:
                                self.count_friends_step2[str(side)][name_user_response] = js_data_api_f['data']["user"]["edge_followed_by"]["count"]

                        sum_count_f = -1
                        if str(1) and str(2) in self.followers_name_friends_dict:
                            len1 = len(self.count_friends_step2['1'].keys())
                            len2 = len(self.count_friends_step2['2'].keys())
                            if (int(len1) + int(len2)) == \
                                    (len(self.followers_name_dict[self.user1]) +
                                     len(self.followers_name_dict[self.user2]) - self.counter_filtered):

                                all_sum = 0
                                for key, value in self.count_friends_step2['1'].items():
                                    all_sum += value
                                for key, value in self.count_friends_step2['2'].items():
                                    all_sum += value
                                sum_count_f = all_sum
                        else:
                            pass

                        result_f = js_data_api_f['data']["user"]["edge_followed_by"]["edges"]
                        for item_f in result_f:
                            name_of_user_f = item_f["node"]["username"]
                            self.followers_name_friends_dict[str(side)][name_user_response].add(str(name_of_user_f))

                        if check_next_f is True:
                            yield response.follow(
                                f"{self.api_url}?{urlencode(self.get_pagination_for_api(js_data_api_f, id_user_response))}",
                                callback=self.step_one_followers_parse, meta={
                                    # 'cookiejar': response.meta['cookiejar'],
                                    "id": str(id_user_response),
                                                                              "user_name": name_user_response,
                                                                              "side": side})
                        if check_next_f is False:
                            sum_local = 0
                            if '1' and '2' in self.followers_name_friends_dict:
                                followers_followers_by_user1 = {"all": set()}
                                followers_followers_by_user2 = {"all": set()}
                                for key, value in self.followers_name_friends_dict['1'].items():
                                    sum_local += len(value)
                                    for item in value:
                                        followers_followers_by_user1["all"].add(str(item))
                                for key, value in self.followers_name_friends_dict['2'].items():
                                    sum_local += len(value)
                                    for item in value:
                                        followers_followers_by_user2["all"].add(str(item))
                                print(f"sum_local={sum_local} sum_count_f={sum_count_f}")
                                print(f"sum counters={sum(self.count_friends_step2['1'].values()) + sum(self.count_friends_step2['2'].values())}")

                                if sum_local == sum_count_f:
                                    non_unique_f = followers_followers_by_user1["all"].intersection(
                                        followers_followers_by_user2["all"])
                                    if non_unique_f != set():
                                        print(
                                            f"Следующие пользователи {non_unique_f} есть одновременно в подписчиках у {self.user1} и {self.user2}")
                                        self.non_unique_counter_f = len(non_unique_f)
                                        for user_in_followers_f in non_unique_f:
                                            came_from1 = str
                                            came_from2 = str
                                            for key, value in self.followers_name_friends_dict['1'].items():
                                                if user_in_followers_f in value:
                                                    came_from1 = str(key)
                                            for key, value in self.followers_name_friends_dict['2'].items():
                                                if user_in_followers_f in value:
                                                    came_from2 = str(key)
                                            yield response.follow(f"https://www.instagram.com/{user_in_followers_f}",
                                                                  callback=self.one_friend_parse_step2,
                                                                  meta={
                                                                      # 'cookiejar': response.meta['cookiejar'],
                                                                      "user_name": user_in_followers_f,
                                                                        "came_from1": came_from1,
                                                                        "came_from2": came_from2
                                                                        })
                                    if non_unique_f == set():
                                        print("Эта часть кода еще не доработана! if name_user_response not in self.accounts_list")
                                        print("Ожидает доработки. Здесь начинается этап 3.")

    # ШАГ 1, если есть совпадения.
    def one_friend_parse(self, response):
        js_data_friend = self.get_js_data_extract(response)
        user_name_f = response.meta["user_name"]

        yield response.follow(f"{self.api_url}?{urlencode(self.get_pagination(js_data_friend))}",
                              callback=self.one_friend_next_parse,
                              meta={'id': str(js_data_friend['entry_data']['ProfilePage'][0]['graphql']['user']['id']),
                                    "user_name": user_name_f,
                                    })

    def one_friend_next_parse(self, response):
        id_user_response_one = response.meta['id']
        name_user_response_one = response.meta['user_name']

        if name_user_response_one not in self.follower_one_dict:
            self.follower_one_dict[name_user_response_one] = set()

        print(f"Провожу проверку пользователя {name_user_response_one}")
        js_data_api_one = response.json()
        check_next = js_data_api_one["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]

        result = js_data_api_one['data']["user"]["edge_followed_by"]["edges"]
        for item in result:
            name_of_user = item["node"]["username"]
            self.follower_one_dict[name_user_response_one].add(str(name_of_user))

        if check_next is True:
            yield response.follow(
                f"{self.api_url}?{urlencode(self.get_pagination_for_api(js_data_api_one, id_user_response_one))}",
                callback=self.one_friend_next_parse, meta={"id": str(id_user_response_one),
                                                           "user_name": name_user_response_one})

        if check_next is False:
            self.one_friend_next_parse_counter += 1
            if self.user1 in self.follower_one_dict[name_user_response_one] \
                    and self.user2 in self.follower_one_dict[name_user_response_one]:
                print(f"пользователь {name_user_response_one} найден в подписчках у {self.user1} и {self.user2}. "
                      f"Этап 1. Два пользователя знакомы через {name_user_response_one}.")

            if self.user1 not in self.follower_one_dict[name_user_response_one] \
                    or self.user2 not in self.follower_one_dict[name_user_response_one]:
                print(f"Рукопожатие не состоялось.")
                if self.one_friend_next_parse_counter == self.non_unique_counter:
                    print("Ищу дальше...")
                    self.one_friend_next_parse_counter = 0
                    local_list = [self.followers_name_dict[self.user1], self.followers_name_dict[self.user2]]
                    for num, sett in enumerate(local_list):
                        for one_user in sett:
                            yield response.follow(f"https://www.instagram.com/{one_user}",
                                      callback=self.user_page_parse,
                                      meta={"user_name": one_user,
                                            "side": (num + 1)})

    # ШАГ 2, если есть совпадения.
    def one_friend_parse_step2(self, response):
        js_data_friend_2 = self.get_js_data_extract(response)
        user_name_f2 = response.meta["user_name"]
        came_from1 = response.meta["came_from"]
        came_from2 = response.meta["came_from"]

        yield response.follow(f"{self.api_url}?{urlencode(self.get_pagination(js_data_friend_2))}",
                              callback=self.one_friend_next_parse_step2,
                              meta={'id': str(js_data_friend_2['entry_data']['ProfilePage'][0]['graphql']['user']['id']),
                                    "user_name": user_name_f2,
                                    "came_from1": came_from1,
                                    "came_from2": came_from2
                                    })

    def one_friend_next_parse_step2(self, response):
        id_user_response_one2 = response.meta['id']
        name_user_response_one2 = response.meta['user_name']
        came_from1 = response.meta["came_from"]
        came_from2 = response.meta["came_from"]

        if name_user_response_one2 not in self.follower_one_dict_step2:
            self.follower_one_dict_step2[name_user_response_one2] = set()

        print(f"Провожу проверку пользователя {name_user_response_one2}")
        js_data_api_one2 = response.json()
        check_next = js_data_api_one2["data"]["user"]["edge_followed_by"]["page_info"]["has_next_page"]

        result2 = js_data_api_one2['data']["user"]["edge_followed_by"]["edges"]
        for item2 in result2:
            name_of_user2 = item2["node"]["username"]
            self.follower_one_dict_step2[name_user_response_one2].add(str(name_of_user2))

        if check_next is True:
            yield response.follow(
                f"{self.api_url}?{urlencode(self.get_pagination_for_api(js_data_api_one2, id_user_response_one2))}",
                callback=self.one_friend_next_parse_step2, meta={"id": str(id_user_response_one2),
                                                           "user_name": name_user_response_one2,
                                                                 "came_from1": came_from1,
                                                                    "came_from2": came_from2})

        if check_next is False:
            self.one_friend_next_parse_counter2 += 1
            if came_from1 in self.follower_one_dict_step2[name_user_response_one2] \
                    and came_from2 in self.follower_one_dict_step2[name_user_response_one2]:

                print(f"Пользователь {name_user_response_one2} найден в подписчках у {came_from1} и {came_from2}. "
                      f"Этап 2. Цепочка рукопожатия:  {self.user1} --> {came_from1} --> {name_user_response_one2}"
                      f" --> {came_from2} --> {self.user2}.")

            if came_from1 not in self.follower_one_dict_step2[name_user_response_one2] \
                    or came_from2 not in self.follower_one_dict_step2[name_user_response_one2]:
                print(f"Рукопожатие не состоялось.")
                if self.one_friend_next_parse_counter2 == self.non_unique_counter_f:
                    print("Ищу дальше...")
                    self.one_friend_next_parse_counter2 = 0

                    print('ДАЛЬШЕ НАЧИНАЕТСЯ ЭТАП 3 !!!!!!!!!!!!!!!!!!!!')
                    # for numb, side_1_2 in enumerate(self.followers_name_friends_dict):
                    #     for key1, value1 in side_1_2:
                    #         for key2, value2 in value1:
                    #             for userr in value2:
                    #                 yield response.follow(f"https://www.instagram.com/{userr}",
                    #                                       callback=self.user_page_parse,
                    #                                       meta={"user_name": userr,
                    #                                             "side": (numb + 3)})

    def get_pagination(self, js_data: dict):
        dict_variables = {
            "id": js_data['entry_data']['ProfilePage'][0]['graphql']['user']['id'],
            'include_reel': 'true',
            'fetch_mutual': 'false',
            'first': 66,
        }
        query = {"query_hash": "5aefa9893005572d237da5068082d8d5", "variables": json.dumps(dict_variables)}
        return query

    def get_pagination_for_api(self, js_data_api: dict, id_user_response: str):
        dict_variables = {
            "id": id_user_response,
            'include_reel': 'true',
            'fetch_mutual': 'false',
            'first': 66,
            'after': js_data_api["data"]["user"]["edge_followed_by"]["page_info"]["end_cursor"]
        }
        query = {"query_hash": "5aefa9893005572d237da5068082d8d5", "variables": json.dumps(dict_variables)}
        return query

    def get_js_data_extract(self, response):
        script = response.xpath(
            "//script[contains(text(), 'window._sharedData = ')]/text()"
        ).extract_first()
        return json.loads(script.replace("window._sharedData = ", "")[:-1])