from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from my_gb_parse.spiders.my_autoyola import MyAutoyolaSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("my_gb_parse.settings")
    crawler_proc = CrawlerProcess(settings=crawler_settings)
    crawler_proc.crawl(MyAutoyolaSpider)
    crawler_proc.start()
