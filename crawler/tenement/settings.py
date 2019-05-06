BOT_NAME = 'tenement'

SPIDER_MODULES = ['tenement.spiders']
NEWSPIDER_MODULE = 'tenement.spiders'


import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 10

CONCURRENT_REQUESTS_PER_DOMAIN = 1

COOKIES_ENABLED = False

TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}
#
# SPIDER_MIDDLEWARES = {
# }

DOWNLOADER_MIDDLEWARES = {
    'tenement.middlewares.RandomUserAgentMiddlware': 100,
    # 'tenement.middlewares.ProxyMiddleware': 200,
    'tenement.middlewares.DownloadRetryMiddleware': 300,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
}

ITEM_PIPELINES = {
    'tenement.pipelines.TenementPipeline': 100,
    'tenement.pipelines.DuplicatesPipeline': 200,
    'scrapy.pipelines.images.ImagesPipeline': 300,
    'tenement.pipelines.ESPipeline': 400,
}

project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGES_STORE =  os.path.join(project_dir, 'data/images')

MEDIA_ALLOW_REDIRECTS = True

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 10
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 10
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 3

# 邮件相关设置
MAIL_FROM = 'bobbie_liu88@163.com'
MAIL_HOST = 'smtp.163.com'
MAIL_PORT = 25
MAIL_USER = 'bobbie_liu88@163.com'
# 邮箱授权码
MAIL_PASS = '123456d'
# 邮件接收者列表
RECEIVE_LIST = ['dev.bobbie@gmail.com','153247605@qq.com']

# 邮件主题
SUBJECT = '爬虫状态报告'


# 代理服务器
PROXY_SERVER = "http://http-cla.abuyun.com:9030"
# 代理服务器隧道验证信息
PROXY_USER = "HSAM1367RL55808C"
PROXY_PASS = "4AE087EF4788C11C"

# ES 节点, 可以配置多个节点(集群), 默认为 None, 不会存储到 ES
ELASTIC_HOSTS = [
    {'host': 'elastic', 'port': 9200},
]

REDIS_HOST = 'redis'  # 默认为 None, 不会去重
REDIS_PORT = 6379  # 默认 6379