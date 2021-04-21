from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from lesson6.avito_parse.spiders.my_avito import MyAvitoSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("avito_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(MyAvitoSpider)
    crawler_proc.start()
