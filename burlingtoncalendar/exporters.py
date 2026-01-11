
from scrapy.exporters import BaseItemExporter


import icalendar
from uuid import UUID, uuid5

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

        e.add("dtstart", icalendar.vDatetime(item['start_datetime']))
        e.add("dtend", icalendar.vDatetime(item['end_datetime']))
        e.add("dtstamp", icalendar.vDatetime(item['dtstamp_updated_at_datetime']))

        e.add('uid', icalendar.vText(uuid5(ns, item['detail_url'])))
        e.add('url', icalendar.vText(item['detail_url']))

        # print(item['start_datetime'], type(item['start_datetime']), dir(item['start_datetime']))
        self.cal.add_component(e)


    def finish_exporting(self):
        self.cal.add_missing_timezones()
        self.cal.subcomponents = sorted(self.cal.subcomponents, key=lambda e: e.get("UID"))  # stable ordering; sort top-level subcomponents by UID
        self.file.write(self.cal.to_ical(sorted=True))  # stable ordering; sort properties
