import scrapy
from datetime import datetime
import re
from burlingtoncalendar.items import Meeting
import logging
import icalendar
from typing import Generator

class OakvilleCouncilMeetingsSpider(scrapy.Spider):
    name = "oakvillecouncilmeetings"
    allowed_domains = ["pub-oakville.escribemeetings.com"]
    start_urls = ["https://pub-oakville.escribemeetings.com/?meetingviewid=2"]

    def parse(self, response):
        """
        Parse the main page and extract meeting information from each upcoming meeting container.
        """
        self.logger.info("Parsing Oakville Council Meetings page")
        
        # Find all upcoming meeting containers
        for meeting_container in response.css('div.upcoming-meeting-container'):
            # Extract basic meeting information
            
            # Extract title
            title_element = meeting_container.css('div.meeting-header h3.meeting-title-heading span::text, div.meeting-header h3.meeting-title-heading a::text').get()
            title = title_element.strip() if title_element else "Unknown Meeting"
            
            # Extract date and time
            date_text = meeting_container.css('div.meeting-date::text').get()
            start_datetime = None
            if date_text:
                date_text = date_text.strip()
                try:
                    start_datetime = datetime.strptime(date_text, "%A, %d %B %Y @ %I:%M %p")
                except ValueError as e:
                    self.logger.error(f"Error parsing date/time: {e}")
            
            # Extract location
            location = meeting_container.css('div.startLocation::text').get()
            location = location.strip() if location else "Unknown Location"
            
            # Extract detail URL if available
            detail_url = meeting_container.css('div.meeting-title h3.meeting-title-heading a::attr(href)').get()
            if detail_url:
                detail_url = response.urljoin(detail_url)
            else:
                # Provide a fallback URL to avoid None - using the page URL with a unique identifier
                detail_url = f"{response.url}#{title}_{date_text}"
            
            # Extract video URL if available
            video_url = meeting_container.css('a.link[href*="VideoStream.aspx"]::attr(href)').get()
            if video_url:
                video_url = response.urljoin(video_url)
            
            # Extract agenda links
            agendas = []
            for agenda in meeting_container.css('ul.resource-list li a[href*="Agenda"]'):
                link = agenda.css('::attr(href)').get()
                if link:
                    agendas.append(response.urljoin(link))
            
            # Extract minutes link
            minutes_link = None
            for minute in meeting_container.css('ul.resource-list li a[href*="minute"], ul.resource-list li a[href*="Minute"]'):
                link = minute.css('::attr(href)').get()
                if link:
                    minutes_link = response.urljoin(link)
                    break
            
            # Extract additional documents
            package = []
            for doc in meeting_container.css('ul.resource-list li a:not([href*="Agenda"]):not([href*="minute"]):not([href*="Minute"])'):
                link = doc.css('::attr(href)').get()
                if link:
                    package.append(response.urljoin(link))
            
            # Set detail_url according to preference order
            if minutes_link:
                detail_url = minutes_link
            elif agendas:
                detail_url = agendas[0]
            else:
                detail_url = "about:blank"
            
            # Extract meeting type
            meeting_type = title
            
            # If there's a real detail URL, follow it to get more information
            if detail_url != "about:blank" and meeting_container.css('div.meeting-title h3.meeting-title-heading a::attr(href)').get():
                original_detail_url = response.urljoin(meeting_container.css('div.meeting-title h3.meeting-title-heading a::attr(href)').get())
                yield scrapy.Request(
                    original_detail_url,
                    callback=self.parse_meeting_details,
                    cb_kwargs={
                        "title": title,
                        "start_datetime": start_datetime,
                        "location": location,
                        "detail_url": detail_url,  # Already set according to preference
                        "video_url": video_url,
                        "agendas": agendas,
                        "package": package,
                        "meeting_type": meeting_type,
                        "minutes_link": minutes_link
                    }
                )
            else:
                # If no detail URL, create a meeting item with available information
                item = Meeting(
                    title=title,
                    start_datetime=start_datetime,
                    end_datetime=start_datetime.replace(hour=start_datetime.hour+2) if start_datetime else None,
                    dtstamp_updated_at_datetime=datetime.now(),
                    event_details_description=f"Location: {location}",
                    detail_url=detail_url,  # Already set according to preference
                    video_url=video_url,
                    agendas=agendas,
                    package=package,
                    meeting_type=meeting_type
                )
                yield item
        
        # Check if there's pagination and follow next page if available
        next_page = response.css('a.pagination-next::attr(href), a.next-page::attr(href)').get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parse_meeting_details(self, response, title=None, start_datetime=None, location=None, 
                             detail_url=None, video_url=None, agendas=None, package=None, 
                             meeting_type=None, minutes_link=None):
        """
        Parse detailed meeting page to extract more information.
        """
        self.logger.info(f"Parsing meeting details for: {title}")
        
        # Try to extract more detailed description
        description = response.css('div.meeting-description::text, div.meeting-details::text').getall()
        if description:
            description = "\n".join([d.strip() for d in description if d.strip()])
        else:
            description = f"Location: {location}"
        
        # Check if there are any new minutes links on the detail page
        if not minutes_link:
            minutes_links = response.css('a[href*="minute"], a[href*="Minute"]::attr(href)').getall()
            if minutes_links:
                minutes_link = response.urljoin(minutes_links[0])
        
        # Check if there are new agenda links on the detail page
        if not agendas:
            new_agendas = response.css('a[href*="Agenda"]::attr(href)').getall()
            for agenda in new_agendas:
                agendas.append(response.urljoin(agenda))
        
        # Re-apply the preference order for detail_url
        if minutes_link:
            detail_url = minutes_link
        elif agendas:
            detail_url = agendas[0]
        else:
            detail_url = "about:blank"
        
        # Check if there's an iCal link
        ical_link = response.css('a[href*=".ics"], a[href*="ical"], a[href*="calendar"]::attr(href)').get()
        
        if ical_link:
            yield scrapy.Request(
                response.urljoin(ical_link),
                callback=self.handle_ical_file,
                cb_kwargs={
                    "title": title,
                    "description": description,
                    "meeting_type": meeting_type,
                    "detail_url": detail_url,  # Set according to preference
                    "video_url": video_url,
                    "agendas": agendas,
                    "package": package,
                    "location": location
                }
            )
        else:
            # If no iCal link, create a meeting item with the information we have
            end_datetime = start_datetime.replace(hour=start_datetime.hour+2) if start_datetime else None
            
            item = Meeting(
                title=title,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                dtstamp_updated_at_datetime=datetime.now(),
                event_details_description=description,
                detail_url=detail_url,  # Set according to preference
                video_url=video_url,
                agendas=agendas,
                package=package,
                meeting_type=meeting_type
            )
            yield item
    
    def handle_ical_file(self, response, detail_url, title, description, meeting_type,
                        video_url=None, agendas=None, package=None, location=None) -> Generator[Meeting, None, None]:
        """
        Parse iCal file to get structured meeting information.
        """
        # detail_url should already be set according to preference
        # but ensure it's not None as a safety check
        if not detail_url:
            if agendas:
                detail_url = agendas[0]
            else:
                detail_url = "about:blank"
        
        try:
            source_calendar = icalendar.Calendar.from_ical(response.body)
            
            for component in source_calendar.walk():
                if component.name == "VEVENT":
                    start_datetime = component.decoded('dtstart') if 'dtstart' in component else None
                    end_datetime = component.decoded('dtend') if 'dtend' in component else None
                    dtstamp = component.decoded('dtstamp') if 'dtstamp' in component else datetime.now()
                    
                    event_summary = str(component.get('summary', '')) if 'summary' in component else title
                    
                    item = Meeting(
                        title=event_summary,
                        start_datetime=start_datetime,
                        end_datetime=end_datetime,
                        dtstamp_updated_at_datetime=dtstamp,
                        event_details_description=description,
                        detail_url=detail_url,  # This will never be None now
                        video_url=video_url,
                        agendas=agendas,
                        package=package,
                        meeting_type=meeting_type
                    )
                    yield item
                    return  # Assuming one event per iCal file
            
            # If no event found in the iCal, create a meeting item with the information we have
            self.logger.warning("No events found in iCal file, using existing information")
            item = Meeting(
                title=title,
                start_datetime=None,
                end_datetime=None,
                dtstamp_updated_at_datetime=datetime.now(),
                event_details_description=description,
                detail_url=detail_url,  # This will never be None now
                video_url=video_url,
                agendas=agendas,
                package=package,
                meeting_type=meeting_type
            )
            yield item
            
        except Exception as e:
            self.logger.error(f"Error parsing iCal file: {e}")
            # If error parsing iCal, create a meeting item with the information we have
            item = Meeting(
                title=title,
                start_datetime=None,
                end_datetime=None,
                dtstamp_updated_at_datetime=datetime.now(),
                event_details_description=f"Location: {location}\n{description}",
                detail_url=detail_url,  # This will never be None now
                video_url=video_url,
                agendas=agendas,
                package=package,
                meeting_type=meeting_type
            )
            yield item
