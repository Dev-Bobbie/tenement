# -*- coding: utf-8 -*-
import time

from scrapy.linkextractors import LinkExtractor
from scrapy.mail import MailSender
from scrapy.spiders import CrawlSpider, Rule

from tenement.items import TenementItemLoader, spider_58Item


class A_58_Spider(CrawlSpider):
    start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    name = 'spider_58'
    allowed_domains = ['58.com']
    start_urls = ['https://sh.58.com/chuzu/']

    rules = (
        Rule(LinkExtractor(restrict_css='.next'),follow=True),
        Rule(LinkExtractor(restrict_css='.des > h2'), callback='parse_item'),
    )

    def parse_item(self, response):
        if response.status not in [200,201]:
            self.crawler.stats.inc_value("Failed_Reqeust")

        try:
            # 使用Crawl api记录文章详情页请求成功的Request
            self.crawler.stats.inc_value("Info_Detail_Success_Reqeust")
        except Exception as e:
            _ = e

        item_loader = TenementItemLoader(item=spider_58Item(),response=response)

        item_loader.add_css(field_name='title', css='div.house-title > h1::text')
        item_loader.add_value(field_name='source', value=self.name)
        item_loader.add_css(field_name='author', css='a.c_000::text')
        item_loader.add_css(field_name='image_urls', css='#housePicList li > img::attr(lazy_src)')
        item_loader.add_css(field_name='author_link', css='a.c_000::attr(href)')
        item_loader.add_css(field_name='housing_type', css='span.strongbox::text',re=r'\s*(.*)\s*')
        item_loader.add_value(field_name='source_url', value=response.url)
        item_loader.add_css(field_name='publish_time', css='p.house-update-info::text',re=r'.*?(\d+.*).*')
        item_loader.add_css(field_name='price', css='b.f36::text')
        item_loader.add_css(field_name='author_phone', css='span.house-chat-txt::text')
        item_loader.add_xpath(field_name='rent_type', xpath='//ul[@class="f14"]/li[1]/span[2]/text()')
        item_loader.add_css(field_name='area', css='span.dz::text')
        item_loader.add_xpath(field_name='detail', xpath='//span[@class="a2"]//text()', re=r'\s*(.*)\s*')

        info_item = item_loader.load_item()

        yield info_item

    def close(self, reason):
        """
        爬虫邮件报告状态
        """
        # 结束时间
        fnished = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # 创建邮件发送对象
        mail = MailSender.from_settings(self.settings)
        # 邮件内容
        spider_name = self.settings.get('BOT_NAME')
        start_time = self.start
        artice_success_request = self.crawler.stats.get_value("Info_Detail_Success_Reqeust")
        failed_request = self.crawler.stats.get_value("Failed_Reqeust")
        # 若请求成功, 则默认为0
        if failed_request == None:
            failed_request = 0
        insert_into_success = self.crawler.stats.get_value("Success_InsertedInto_ES")
        failed_db = self.crawler.stats.get_value("Failed_InsertInto_ES")
        # 若插入成功, 则默认为0
        if failed_db == None:
            failed_db = 0
        fnished_time = fnished
        body = "爬虫名称: {}\n\n 开始时间: {}\n\n 请求成功总量：{}\n\n 请求失败总量：{} \n\n 数据库存储总量：{}\n 数据库存储失败总量：{}\n\n 结束时间  : {}\n".format(
            spider_name,
            start_time,
            artice_success_request,
            failed_request,
            insert_into_success,
            failed_db,
            fnished_time)
        try:
            # 发送邮件
            mail.send(to=self.settings.get('RECEIVE_LIST'), subject=self.settings.get('SUBJECT'), body=body)
        except Exception as e:
            self.logger.error("Send Email Existing")
