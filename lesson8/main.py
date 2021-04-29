import os
import dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from lesson8.instag_parse.spiders.my_insta import InstaSpider


dotenv.load_dotenv('.env')
accounts_list = ["doc.tsoy", "maximreznikliberal"]
file = 'graph.txt'

if __name__ == '__main__':
    crawl_settings = Settings()
    crawl_settings.setmodule('instag_parse.settings')

    crawl_proc = CrawlerProcess(settings=crawl_settings)
    crawl_proc.crawl(InstaSpider,
                     login=os.getenv('UNM'),
                     password=os.getenv('ENC_PASSWORD'),
                     accounts_list=accounts_list,
                     file = file)
    crawl_proc.start()