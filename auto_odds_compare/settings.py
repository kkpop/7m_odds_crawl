# -*- coding: utf-8 -*-

# Scrapy settings for auto_odds_compare project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'auto_odds_compare'

SPIDER_MODULES = ['auto_odds_compare.spiders']
NEWSPIDER_MODULE = 'auto_odds_compare.spiders'

# 保存暂停前的爬虫任务
JOBDIR='spider_odds_7m'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'auto_odds_compare (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   'auto_odds_compare.middlewares.AutoOddsCompareSpiderMiddleware': 543,
   'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'auto_odds_compare.middlewares.AutoOddsCompareSpiderMiddleware': 543,
    'scrapy.downloadermiddleware.useragent.UserAgentMiddleware': None,
    # 'scrapy.downloadermiddleware.retry.RetryMiddleware': None,
    'auto_odds_compare.spiders.rotate_useragent.RotateUserAgentMiddleware': 400,
    # 'auto_odds_compare.middlewares.RetryMiddleware': 450,
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}
DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
SPLASH_URL = 'http://192.168.99.100:8050/'

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   'auto_odds_compare.pipelines.AutoOddsComparePipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'


# Redis 分布式
SCHEDULER = "scrapy_redis.scheduler.Scheduler"  #启用Redis调度存储请求队列
SCHEDULER_PERSIST = True    #不清除Redis队列、这样可以暂停/恢复 爬取
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"  #确保所有的爬虫通过Redis去重
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderPriorityQueue'
REDIS_HOST = '127.0.0.1'  # 也可以根据情况改成 localhost
REDIS_PORT = 6379
REDIS_URL = None
