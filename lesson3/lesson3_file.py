# Урок 3, задача 1.
"""
Источник https://geekbrains.ru/posts/
Необходимо обойти все записи в блоге и извлечь из них информацию следующих полей:
+ url страницы материала
+ Заголовок материала
+ Первое изображение материала (Ссылка)
+ Дата публикации (в формате datetime)
+ имя автора материала
+ ссылка на страницу автора материала
+ комментарии в виде (автор комментария и текст комментария)
+ список тегов

реализовать SQL структуру хранения данных cо следующими таблицами:
Post
Comment
Writer
Tag.
Организовать реляционные связи между таблицами.

При сборе данных учесть, что полученый из данных автор уже может быть в БД и значит необходимо это заблаговременно
 проверить.
Не забываем закрывать сессию по завершении работы с ней.
"""

# pip install sqlalchemy
# pip install databases
# pip install databases[sqlite]
# pip install databases[mysql]
from urllib.parse import urljoin
import datetime
import bs4
import requests
from database.database import Database

class GbBlogParse:
    def __init__(self, start_url, database: Database):
        self.db = database
        self.start_url = start_url
        self.done_urls = set()
        self.tasks = [
            self.get_task(self.start_url, self.parse_feed),
        ]
        self.done_urls.add(self.start_url)

    def get_task(self, url, callback):
        def task():
            soup = self._get_soup(url)
            return callback(url, soup)
        return task

    def _get_response(self, url):
        response = requests.get(url)
        return response

    def _get_soup(self, url):
        soup = bs4.BeautifulSoup(self._get_response(url).text, "lxml")
        return soup

    def parse_feed(self, url, soup):
        pag_ul = soup.find("ul", attrs={"class": "gb__pagination"})
        pag_urls = set(
                    urljoin(url, pag_a.attrs["href"])
                    for pag_a in pag_ul.find_all("a")
                    if pag_a.attrs.get("href")
        )
        for pag_url in pag_urls:
            if pag_url not in self.done_urls:
                self.tasks.append(self.get_task(pag_url, self.parse_feed))

        post_items = soup.find("div", attrs={"class": "post-items-wrapper"})
        posts = set(
            urljoin(url, post_a.attrs.get("href"))
            for post_a in post_items.find_all("a", attrs={"class": "post-item__title"})
            if post_a.attrs.get("href")
        )

        for post_url in posts:
            if post_url not in self.done_urls:
                self.tasks.append(self.get_task(post_url, self.parse_post))

    def parse_post(self, url, soup):
        author_tag = soup.find("div", attrs={"itemprop": "author"})

        get_post_id = soup.find('comments').attrs.get('commentable-id')
        response = self._get_response(urljoin(self.start_url,
                                    f"/api/v2/comments?commentable_type=Post&commentable_id={get_post_id}&order=desc"))
        data_comments = response.json()

        data = {
            "post_data": {
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                "url": url,
                "id": soup.find("comments").attrs.get("commentable-id"),
                "image_url": soup.select("img[src^=http]")[0]['src'],
                "publication_date": datetime.datetime.strptime((soup.find("time",
                                                                          attrs={"class": "text-md"})['datetime'][:10]),
                                                               '%Y-%m-%d')
            },
            "author_data": {
                "url": urljoin(url, author_tag.parent.attrs.get("href")),
                "name": author_tag.text,
            },
            "tags_data": [
                {"name": tag.text, "url": urljoin(url, tag.attrs.get("href"))}
                for tag in soup.find_all("a", attrs={"class": "small"})
            ],
            "comments_text": data_comments
        }
        return data

    def run(self):
        for task in self.tasks:
            task_result = task()
            if task_result:
                self.db.create_post(task_result)

    def save(self, data):
        self.db.create_post(data)


if __name__ == "__main__":
    database = Database("sqlite:///gb_blog.db")
    parser = GbBlogParse("https://gb.ru/posts", database)
    parser.run()