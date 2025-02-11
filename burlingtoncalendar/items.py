# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html


from datetime import date
from scrapy.item import Item, Field
from itemloaders.processors import TakeFirst  # provided by scrapy


class Meeting(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    
    title = Field()

    start_datetime = Field()
    end_datetime = Field()
    dtstamp_updated_at_datetime = Field()

    detail_url = Field()

    video_url = Field()
    agendas = Field()
    package = Field()

    meeting_type = Field()
    event_details_description = Field()

    contact = Field()
