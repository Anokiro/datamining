import scrapy
import json
import pickle
import sys
from urllib.parse import urlencode


class InstaSpider(scrapy.Spider):
    name = 'instasearch'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    login_url = 'https://www.instagram.com/accounts/login/ajax/'
    url_api = 'https://www.instagram.com/graphql/query/'

    query_hash = {'following': '3dec7e2c57367ef3da3d987d89f9dbc8', 'followers': '5aefa9893005572d237da5068082d8d5'}
    variables = {"id": '', 'include_reel': 'true', 'fetch_mutual': 'false', 'first': 100, 'after': ''}
    temporary_storage = {}
    graph = {'target_user': [], 'have_any_way': False, 'way_list': [], 'data': {'1': {'all': set(), },
                                                                                '2': {'all': set(), }}}

    def __init__(self, login, password, accounts_list, file, *args, **kwargs):
        self.login = login
        self.file = file
        self.password = password
        self.accounts_list = accounts_list
        super(InstaSpider, self).__init__(*args, **kwargs)
        self.graph['target_user'].append(accounts_list[0])
        self.graph['target_user'].append(accounts_list[1])

    def parse(self, response, **kwargs):
        try:
            js_data = self.get_js_data_extract(response)
            yield scrapy.FormRequest(
                self.login_url,
                method='POST',
                callback=self.parse,
                formdata={
                    'username': self.login,
                    'enc_password': self.password,
                },
                headers={'X-CSRFToken': js_data['config']['csrf_token']}
            )
        except AttributeError:
            try:
                with open(self.file, 'rb') as my_file:
                    data_file = pickle.load(my_file)
                    if data_file['target_user'] == self.graph['target_user']:
                        if data_file['have_any_way']:
                            if len(data_file['way_list']):
                                sys.exit()
                            else:
                                sys.exit()
                        else:
                            self.graph['data'] = data_file['data']
                    else:
                        sys.exit()
            except FileNotFoundError:
                with open(self.file, 'wb') as my_file:
                    pickle.dump(self.graph, my_file)
            if response.json().get('authenticated'):
                for number, user in enumerate(self.accounts_list):
                    yield response.follow(f'/{user}', callback=self.get_graph, meta={'side': str(number + 1)})

    def get_graph(self, response):
        js_data = self.get_js_data_extract(response)
        side = response.meta['side']
        id = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
        self.graph['data'][side]['all'].add(id)
        for hash in self.query_hash.keys():
            url_api = self.get_api_url(id, hash)
            yield response.follow(url_api, callback=self.parse_api, meta={'follow': hash, 'id': id, 'side': side})

    def parse_api(self, response):
        follow = response.meta['follow']
        id = response.meta['id']
        side = response.meta['side']
        data = json.loads(response.body)
        if (id not in self.graph['data'][side]) or (not len(self.graph['data'][side][id])):
            if id not in self.temporary_storage:
                self.temporary_storage[id] = {'side': side, 'followers': [], 'following': []}
            if follow == 'followers':
                data = data['data']['user']['edge_followed_by']
                self.temporary_storage[id]['count_followers'] = data['count']
            else:
                data = data['data']['user']['edge_follow']
                self.temporary_storage[id]['count_following'] = data['count']

            for follower in self.get_followers(data):
                self.temporary_storage[id][follow].append(follower)

            while data['page_info']['has_next_page']:
                after = data['page_info']['end_cursor']
                url_api = self.get_api_url(id, follow, after)
                yield response.follow(
                    url_api, callback=self.parse_api, meta={'follow': follow, 'id': id, 'side': side})

            if ('count_followers' in self.temporary_storage[id]) and ('count_following' in self.temporary_storage[id]):
                if (len(self.temporary_storage[id]['followers']) == self.temporary_storage[id]['count_followers']) \
                        and (len(self.temporary_storage[id]['following']) == self.temporary_storage[id]['count_following']):
                    step1 = set(self.temporary_storage[id]['followers'])
                    step2 = set(self.temporary_storage[id]['following'])
                    step2.intersection_update(step1)
                    item = {'side': self.temporary_storage[id]['side'], 'id': id, 'graph': step2}
                    del self.temporary_storage[id]
                    yield item

        temp_graph = self.graph['data'].copy()
        for side, list in temp_graph.items():
            for id in list['all']:
                if id not in self.graph['data'][side]:
                    self.graph['data'][side][id] = set()
                    for hash in self.query_hash.keys():
                        yield response.follow(self.get_api_url(id, hash), callback=self.parse_api,
                                              meta={'follow': hash, 'id': id, 'side': side})

    def get_api_url(self, id, follow, after=''):
        variables = self.variables.copy()
        variables['id'] = id
        variables['after'] = after
        query = {'query_hash': self.query_hash[follow], 'variables': json.dumps(variables)}
        return f'{self.url_api}?{urlencode(query)}'

    def get_js_data_extract(self, response):
        script = response.xpath('//script[contains(text(), "window._sharedData = ")]/text()').get()
        return json.loads(script.replace("window._sharedData = ", '')[:-1])

    @staticmethod
    def get_followers(data):
        for user in data['edges']:
            yield user['node']['id']