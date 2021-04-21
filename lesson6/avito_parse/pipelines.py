# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
import pymongo


class AvitoParsePipeline:
    def __init__(self):
        client = pymongo.MongoClient()
        self.db = client["avito_parse_lesson6"]

    def process_item(self, item, spider):
        self.db[spider.name].insert_one(item)
        return item

