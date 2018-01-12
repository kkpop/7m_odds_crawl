# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from auto_odds_compare.spiders.tools import MyTools
import pdb

import re
import random
import base64

# from scrapy import log
# from scrapy.contrib.downloadermiddleware.retry import RetryMiddleware as _RetryMiddleware


class AutoOddsCompareSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    # 自定义
    def process_spider_exception(self, response, exception, spider):
        with open(r"error_url.txt", 'a') as f:
            f.write(str(exception) + ': ' + str(response.url))
        return None

    def process_response(self, request, response, spider):
        '''对返回的response处理'''
        if response.status != 200:
            # last_proxy = request.meta.get('proxy')    # 需要用正则表达式找到之前的代理
            # MyTools.delete_proxy(last_proxy)
            proxy = MyTools.get_proxy()
            print("response.status != 200，新的IP:" + str(proxy))
            # 为当前request更换代理，因为使用的是SplashRequset,所以要更改lua_script
            LUA_SCRIPT = """
                        function main(splash)
                            splash:on_request(function(request)
                                request:set_proxy{
                                    host = "%(host)s",
                                    port = %(port)s,
                                    username = '', password = '', type = "HTTPS",
                                }
                            end)
                            assert(splash:go(args.url))
                            assert(splash:wait(0.5))
                            return {
                                html = splash:html(),
                            }
                        end
                        """
            proxy_host = proxy.strip().split(':')[0]
            proxy_port = int(proxy.strip().split(':')[-1])
            request.meta['splash']['args']['lua_source'] = LUA_SCRIPT % {'host': proxy_host, 'port': proxy_port}
            return request
        return response

# class RetryMiddleware(_RetryMiddleware):
#
#     def __init__(self, settings):
#         super(RetryMiddleware, self).__init__(settings)
#         self.proxy = MyTools.get_proxy()
#
#     def _retry(self, request, reason, spider):
#         retries = request.meta.get('retry_times', 0) + 1
#         last_proxy = request.meta.get('proxy')
#
#         if self.proxy or retries <= self.max_retry_times:
#             log.msg(format="Retrying %(request)s (failed %(retries)d times): %(reason)s",
#                     level=log.DEBUG, spider=spider, request=request, retries=retries, reason=reason)
#
#             retryreq = request.copy()
#             retryreq.meta['retry_times'] = retries
#             # retryreq.dont_filter = True
#             retryreq.priority = request.priority + self.priority_adjust
#
#             if self.proxy:
#                 proxy_address = "http://{}".format(str(self.proxy).replace("b'", "").replace("'", ""))
#                 log.msg('Using proxy <%s>, %d proxies left' % (proxy_address, len(self.proxy)))
#                 retryreq.meta['proxy'] = proxy_address
#
#             return retryreq
#         else:
#             log.msg(format="Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
#                     level=log.DEBUG, spider=spider, request=request, retries=retries, reason=reason)
