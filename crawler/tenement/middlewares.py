import base64
import io
import re

from fontTools.ttLib import TTFont
from scrapy import Selector
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from talospider.utils import get_random_user_agent

class RandomUserAgentMiddlware(object):
    """随机更换user-agent"""
    def __init__(self, crawler):
        super(RandomUserAgentMiddlware, self).__init__()
        self.ua = get_random_user_agent()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        request.headers.setdefault('User-Agent', self.ua)

class ProxyMiddleware(object):
    """初始化代理信息"""
    def __init__(self, proxy_server, proxy_user, proxy_pass):
        self.proxy_server = proxy_server
        self.proxy_user = proxy_user
        self.proxy_pass = proxy_pass
        self.proxy_auth = "Basic " + base64.urlsafe_b64encode(bytes((self.proxy_user + ":" + self.proxy_pass), "ascii")).decode("utf8")

    @classmethod
    def from_crawler(cls, crawler):
        # 返回实例对象：cls = class
        return cls(
            proxy_server = crawler.settings.get('PROXY_SERVER'),
            proxy_user = crawler.settings.get('PROXY_USER'),
            proxy_pass = crawler.settings.get('PROXY_PASS')
        )

    def process_request(self, request, spider):
        request.meta["proxy"] = self.proxy_server
        request.headers["Proxy-Authorization"] = self.proxy_auth

    def process_response(self, request, response, spider):
        return response

class DownloadRetryMiddleware(RetryMiddleware):
    """继承Scapy内置重试RetryMiddleware, 仅作微小改动"""
    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) \
                and not request.meta.get('dont_retry', False):
            return self._retry(request, exception, spider)

class FontReplaceMiddleware(object):
    """用解密后的字体替换原页面的加密内容"""
    def process_response(self, request, response, spider):
        try:
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
                            "_body": bytes(response_, encoding='utf-8')
                        })
        except AttributeError as e:
            # 下载图片的时候不用进行字体替换,因此直接返回response
            _ = e
        return response
