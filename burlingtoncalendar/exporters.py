
from scrapy.exporters import BaseItemExporter


import icalendar
import json
from datetime import datetime, date, tzinfo
import pytz
from uuid import uuid5, UUID

from .items import Meeting

ns = UUID('df750e3c-e8ae-11ef-aa47-6e2c6d516a99')


class ICalItemExporter(BaseItemExporter):
    # similar to the XML exporter
    def __init__(self, file, **kwargs):
        super().__init__(dont_fail=True, **kwargs)
        self.file = file  # already-open file handle

        self.cal = icalendar.Calendar()
        self._kwargs.setdefault('ensure_ascii', not self.encoding)

    def start_exporting(self):
        self.cal.add('prodid', '-//BurlingtonOntario//verselogic.net//')
        self.cal.add('version', '2.0')
        self.cal.add('method', 'PUBLISH')

    def export_item(self, item: Meeting):
        e = icalendar.Event()
        
        e.add("summary", icalendar.vText(item['title']))

        d = item['event_details_description']

        if item['detail_url']:
            d += "\n\nDetails: " + item['detail_url']
        
        if item['video_url']:
            d += "\n\nStream: " + item['video_url']
        
        if item['agendas']:
            d += "\n\nAgenda: " + " ".join(item['agendas'])

        if item['package']:
            d += "\n\nPackage: " + " ".join(item['package'])

        e.add("description", icalendar.vText(d))

        e.add("dtstart", item['start_datetime'])
        e.add("dtend", item['end_datetime'])
        e.add("dtstamp", item['dtstamp_updated_at_datetime'])

        e.add('url', icalendar.vText(item['detail_url']))

        # print(item['start_datetime'], type(item['start_datetime']), dir(item['start_datetime']))
        self.cal.add_component(e)


    def finish_exporting(self):
        self.cal.add_missing_timezones()
        self.file.write(self.cal.to_ical())
