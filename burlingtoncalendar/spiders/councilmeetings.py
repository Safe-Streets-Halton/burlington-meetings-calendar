import scrapy

from typing import Generator

import urllib.parse
from scrapy.item import Item
from scrapy.loader import ItemLoader

from burlingtoncalendar.items import Meeting
import json
from datetime import date
import icalendar


class CouncilMeetingsSpider(scrapy.Spider):
    name = 'councilmeetings'
    allowed_domains = ['events.burlington.ca']
    start_urls = [
        'https://events.burlington.ca/meetings/Index' #?Category=Advisory+Committee',
        # 'https://events.burlington.ca/meetings/Index?Category=Committee%20of%20Adjustment'
    ]

    def parse(self, response):
        # https://docs.scrapy.org/en/latest/topics/loaders.html#nested-loaders ?

        for row in response.css("#calMainBody table tbody tr"):
            m = row.css("td:nth-child(2) a::attr(href)").get()
            if '2025-02-10-0930-Committee-of-the-Whole' not in m:
                continue

            video_url = row.css("td:nth-child(3) a::attr(href)").get()
            if video_url:
                video_url = video_url.replace(" ", "%20")
            agendas = [response.urljoin(_) for _ in row.css("td:nth-child(4) a::attr(href)").getall()]
            package = [response.urljoin(_) for _ in row.css("td:nth-child(5) a::attr(href)").getall()]

            yield scrapy.Request(
                response.urljoin(m),
                callback=self.parse_meeting_details,
                cb_kwargs={
                    "video_url": video_url,
                    "agendas": agendas,
                    "package": package
                }
            )
        """
        meeting_urls = response.css("#calMainBody table tbody tr td:nth-child(2) a::attr(href)").getall()

        for m in meeting_urls:
            if '2025-02-10-0930-Committee-of-the-Whole' not in m:
                continue
            yield scrapy.Request(
                response.urljoin(m),
                callback=self.parse_meeting_details,
            )
            break
        """

        # form input Page value always matches request url?
        current_page = int(response.xpath('//form[@id="CalendarSearchForm"]/input[@name="Page"]/@value').get())
        current_page_js = int(response.css("script::text").re_first(r"(?s)\$\('#CalendarPaging'\)\.bootpag\(\s*{.*?page:\s*(\d+),.*?}\s*\)"))
        
        total_pages = int(response.css("script::text").re_first(r"(?s)\$\('#CalendarPaging'\)\.bootpag\(\s*{.*?total:\s*(\d+),.*?}\s*\)"))
        if not total_pages:
            raise ValueError(f"Cannot get total_pages on page {current_page}")

        return
        print(f"Currently on input page {current_page}, js page {current_page_js} of {total_pages}")
        if current_page_js < total_pages:
            next_page_request = scrapy.FormRequest.from_response(
                response,
                method="GET",
                formid='CalendarSearchForm',
                formdata={
                    "Page": str(current_page + 1),  # get the Next page
                    "action": "search",
                }
            )
            yield next_page_request

            """
            2025-02-11 11:30:05 [scrapy.core.engine] DEBUG: Crawled (200) <GET https://events.burlington.ca/meetings/Index?__RequestVerificationToken=n_eYQlxEjTcJ2St8BkEtHqQEnOPwU6VlKOdCXfb6CZcPEXV7nBXT7CC_RkmL4UI9XK7MJyNeljbT-G0nk36fEp2lQ1KZn_EXIbAmSxWC9Zs1&__RequestVerificationToken=QSSCEOqVLh7aUEiRASAK2S-gY56uuHnQMA_QtZ4DC2wm1urOoE_G7Hk0-CsEWbSV1cUIUCO3cDDkyMLXw8qsTPlrel8iOjizW0ti409mF2U1&StartDate=2%2F4%2F2025+12%3A00%3A00+AM&EndDate=2%2F4%2F2026+11%3A59%3A59+PM&Category=Advisory+Committee&Keywords=&Page=2&action=search> (referer: https://events.burlington.ca/meetings/Index?Category=Advisory+Committee)
            """
        
    def parse_meeting_details(self, response, video_url=None, agendas=None, package=None):

        detail_url = response.url

        title = response.css("title::text").get()

        details_chunk = response.css("div.icrt-calendarContentDetail").xpath("./div[2]")

        tx_more = "\n".join([_.strip() for _ in details_chunk.xpath(".//div[@id='tx_more']//text()").getall() if _.strip()])
        tx_less = "\n".join([_.strip() for _ in details_chunk.xpath(".//div[@id='text-less']//text()").getall() if _.strip()])

        if tx_more:
            best_description = tx_more
        elif tx_less:
            best_description = tx_less
        else:
            best_description = "\n".join([_.strip() for _ in details_chunk.xpath(".//div//text()").getall() if _.strip() and _.strip() != "See more"])
        
        category = response.css("div.icrt-calendarContentSideContent").xpath("//h3[contains(., 'Event Categories')]/../..").css(".icrt-calendarContentSideTags span::text").get()

        ical_url = scrapy.Request(
            response.urljoin(
                response.css("a.meta-addCalendar::attr(href)").get()
            ),
            callback=self.handle_ical_file,
            cb_kwargs={
                "title": title,
                "description": best_description,
                "meeting_type": category,
                "detail_url": detail_url,
                "video_url": video_url,
                "agendas": agendas,
                "package": package,
            },

        )

        yield(ical_url)
    
    def handle_ical_file(self, response, detail_url, title, description, meeting_type,
                         video_url=None, agendas=None, package=None) -> Generator[Meeting, None, None]:

        source_calendar = icalendar.Calendar.from_ical(response.body)

        assert len(source_calendar.events) == 1

        source_event: icalendar.Event = source_calendar.events[0]

        m = Meeting(
            detail_url = detail_url,
            title = source_event.get('summary', default=title),
            event_details_description = description,
            meeting_type = meeting_type,

            start_datetime = source_event.decoded('dtstart'),
            end_datetime = source_event.decoded('dtend'),
            dtstamp_updated_at_datetime = source_event.decoded('dtstamp'),

            video_url=video_url,
            agendas=agendas,
            package=package,
        )
        yield m
