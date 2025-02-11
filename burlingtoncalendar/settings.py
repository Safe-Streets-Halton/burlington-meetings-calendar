# Scrapy settings
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'BurlingtonOntarioCalendar'

SPIDER_MODULES = ['burlingtoncalendar.spiders']
NEWSPIDER_MODULE = 'burlingtoncalendar.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'burlingtoncalendar (+https://verselogic.net)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
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
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


FEED_EXPORTERS = {
    'ical': 'burlingtoncalendar.exporters.ICalItemExporter'
}
FEEDS = {
    'dates.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': True,
        'fields': None,
        'indent': 4,
        'item_export_kwargs': {
           'export_empty_fields': True,
        },
        'overwrite': True,
    },
    'dates.jsonlines': {
        'format': 'jsonlines',
        'encoding': 'utf8',
        'store_empty': True,
        'fields': None,
        'indent': 4,
        'item_export_kwargs': {
           'export_empty_fields': True,
        },
        'overwrite': True,
    },
    'dates.ical': {
        'format': 'ical',
        'overwrite': True,
        'item_classes': ["burlingtoncalendar.items.Meeting"],
    },
    'dates.ics': {
        'format': 'ical',
        'overwrite': True,
        'item_classes': ["burlingtoncalendar.items.Meeting"],
    },
    'advisory-committee.ical': {
        'format': 'ical',
        'overwrite': True,
        'item_filter': 'burlingtoncalendar.filters.LocationFilter',
        'meeting_type': 'Advisory Committee',
        'item_classes': ["burlingtoncalendar.items.Meeting"],
    },
}


# DUPEFILTER_DEBUG = True