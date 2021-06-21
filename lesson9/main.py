#pip install python-dotenv
import os
import dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from lesson9.instag_parse.spiders.my_insta import InstagramSpider

if __name__ == "__main__":
    dotenv.load_dotenv(".env")
    crawler_settings = Settings()
    crawler_settings.setmodule("instag_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)

    accounts_list = [
        "_thomas_brain_",
        'anutasemenkova',
                     ]

    crawler_proc.crawl(
        InstagramSpider,
        login=os.getenv("UNM"),
        password=os.getenv("ENC_PASSWORD"),
        accounts_list=accounts_list,
    )
    crawler_proc.start()
