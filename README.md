# Crawl 58同城 - 58同城上海房屋出租爬虫

## 抓取流程

- 以 [58同城上海出租](https://sh.58.com/chuzu/) 的页面为爬取起始点，获取每页所有租房的详情页URL。
- 进入文章详情页，获取租房信息的的标题、发布时间、图片、价格、发布者、详情信息、联系人电话等，并获取房屋的发布者和个人信息链接

## 难点分析

### 1.联系人电话信息以及房屋租金信息获取(字体反爬)

&emsp; 文章中采用了自定义字体来进行反爬,获取到的页面信息必须进行字体解码，再对页面内容进行替换，然后进行正常提取

```python
    def parse_item(self, response):
        base64_str = Selector(text=response.text).re(r"base64,(.*?)'\)")
        if len(base64_str) > 0:
            b = base64.b64decode(base64_str[0])
            font = TTFont(io.BytesIO(b))
            bestcmap = font['cmap'].getBestCmap()
            newmap = dict()
            for key in bestcmap.keys():
                value = int(re.search(r'(\d+)', bestcmap[key]).group(1)) - 1
                key = hex(key)
                newmap[key] = value
            # 把页面上自定义字体替换成正常字体
            response_ = response.text
            for key, value in newmap.items():
                key_ = key.replace('0x', '&#x') + ';'
                if key_ in response_:
                    response_ = response_.replace(key_, str(value))
                    response.__dict__.update({
                        "_cached_ubody": response_,
                        "_body":bytes(response_,encoding='utf-8')
                    })
```

### 2.采用自定义ItemLoader进行数据的提取

&emsp;自定义itemloader增加程序的可配置性,代码看起来更加的简洁清晰

```Python
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
```

### 3. Items数据清洗以及序列化

&emsp;对各个字段数据进行数据清洗，例如时间格式的统一化，房屋价格等

```Python
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
```

### 4. 数据存入Elasticsearch并结合kibana进行相关操作

&emsp; 当解析完页面的信息后，会得到数据，将数据存入ES方便kibana进行操作

```Python
class ESPipeline(object):
    exporter = None

    def open_spider(self, spider):
        self.exporter = ESItemExporter()

    def process_item(self, item, spider):
        try:
            spider.crawler.stats.inc_value('Success_InsertedInto_ES')
        except Exception as e:
            _ = e
            spider.crawler.stats.inc_value('Failed_InsertInto_ES')

        self.exporter.export_item(item)
        return item


from elasticsearch import Elasticsearch
from scrapy.conf import settings
from scrapy.exporters import BaseItemExporter


class ESItemExporter(BaseItemExporter):
    index = 'tenement'
    doc_type = 'info'

    def __init__(self, **kwargs):
        super(ESItemExporter, self).__init__(**kwargs)

        self.elastic_hosts = settings.get('ELASTIC_HOSTS')

        if self.elastic_hosts is not None:
            self.client = Elasticsearch(hosts=self.elastic_hosts)

    def start_exporting(self):
        pass

    def finish_exporting(self):
        pass

    def export_item(self, item):
        if self.client is None:
            return item

        item_id = item['item_id']
        self.client.index(index=self.index, doc_type=self.doc_type, body=dict(item), id=item_id)
        return item
```

### 5.爬虫状态报告

&emsp; 状态报告邮件应该是必不可少的。所以，在之后的每次实战我都将添加该模块功能。

## 结果

&emsp; **爬虫状态邮件**

![Snip20190506_2](https://github.com/Dev-Bobbie/tenement/blob/master/screenshot/Snip20190506_2.png)

&emsp; **文章信息表**

![Snip20190506_4](https://github.com/Dev-Bobbie/tenement/blob/master/screenshot/Snip20190506_4.png)

### 6.docker-compose

```yaml
version: '3.1'
services:
    crawler:
        build: ./crawler
        image: tenement/crawler
        container_name: crawler_58
        networks:
            - localhost
        volumes:
            - ./data:/tenement/data
            - ./data/images:/tenement/data/images
            - ./crawler:/tenement/crawler
        working_dir: /tenement/crawler
        depends_on:
            - redis
            - elastic
        entrypoint: python main.py

    elastic:
        image: docker.elastic.co/elasticsearch/elasticsearch:6.5.0
        container_name: elasticsearch
        environment:
            - bootstrap.memory_lock=true
            - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
        ulimits:
            memlock:
                soft: -1
                hard: -1
        networks:
            - localhost
        ports:
            - 9200:9200
        volumes:
            - ./data/elastic:/usr/share/elasticsearch/data
            - ./data/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml

    kibana:
        image: docker.elastic.co/kibana/kibana:6.5.0
        container_name: kibana
        networks:
            - localhost
        ports:
            - 5601:5601
        environment:
            - ELASTICSEARCH_URL=http://elastic:9200
        depends_on:
            - elastic

    elastic_head:
        image: alivv/elasticsearch-head
        container_name: elastic_head
        networks:
            - localhost
        ports:
            - 9100:9100
        depends_on:
            - elastic

    redis:
        image: redis
        container_name: redis
        networks:
            - localhost
        ports:
            - 6399:6379
        volumes:
            - ./data/redis:/data
networks:
    localhost:
```

运行结果：

![Snip20190506_3](https://github.com/Dev-Bobbie/tenement/blob/master/screenshot/Snip20190506_3.png)

## 帮助

详细说明请看本项目的 [Wiki 页面](https://github.com/Dev-Bobbie/tenement/wiki);