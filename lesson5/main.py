from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from lesson5.hh_parse.spiders.hhru import HhruSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("hh_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(HhruSpider)
    crawler_proc.start()
