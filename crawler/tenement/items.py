# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import datetime
import re
import time
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join, MapCompose, Compose, TakeFirst

def filter_space(value):
    return value.replace(" ","")

def return_images_url(value):
    return value

def publish_time_serializer(value):
    minutes_ago = re.compile(r'.*?(\d+)分钟前.*').search(value)
    hours_ago = re.compile(r'.*?(\d+)小时前.*').search(value)
    days_ago = re.compile(r'.*?(\d+)天前.*').search(value)
    date = re.compile(r'.*?(\d+)-(\d+).*').search(value)

    if minutes_ago:
        publish_time = datetime.datetime.today() - datetime.timedelta(minutes=int(minutes_ago.group(1)))
    elif hours_ago:
        publish_time = datetime.datetime.today() - datetime.timedelta(hours=int(hours_ago.group(1)))
    elif days_ago:
        publish_time = datetime.datetime.today() - datetime.timedelta(days=int(days_ago.group(1)))
    else:
        publish_time = datetime.datetime.today().replace(month=int(date.group(1)), day=int(date.group(2)),hour=0,
                minute=0, second=0)

    if publish_time is not None:
        # return time.mktime(publish_time.timetuple())
        return time.strftime("%Y-%m-%d %H:%M:%S",publish_time.timetuple())

def price_fliter(value):
    return value + "元/月"


class TenementItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()



class TenementItemBaseItem(scrapy.Item):
        item_id = scrapy.Field()
        title = scrapy.Field()
        source = scrapy.Field()
        author = scrapy.Field()
        image_urls = scrapy.Field(output_processor=Compose(return_images_url))
        author_link = scrapy.Field()
        housing_type = scrapy.Field(input_processor=MapCompose(str.strip,filter_space),
                                   output_processor=Compose(Join()))
        source_url = scrapy.Field()
        publish_time = scrapy.Field(input_processor=MapCompose(str.strip,publish_time_serializer))


class spider_58Item(TenementItemBaseItem):
    price = scrapy.Field(input_processor=MapCompose(price_fliter))
    author_phone = scrapy.Field()
    rent_type = scrapy.Field()
    area = scrapy.Field(input_processor=MapCompose(str.strip))
    detail = scrapy.Field(input_processor=MapCompose(str.strip,filter_space),
                        output_processor=Compose(Join()))
