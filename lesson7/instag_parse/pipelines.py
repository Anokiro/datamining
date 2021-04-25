# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter

from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request

class InstagParsePipeline:
    def process_item(self, item, spider):
        return item

class InstagImageDownloadPipline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for url in item.get('images', []):
            yield Request(url)

    def item_completed(self, results, item, info):
        if "images" in item:
            item["images"] = [itm[1] for itm in results]
        return item