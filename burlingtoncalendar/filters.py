

class DefaultAccept:
    def __init__(self, feed_options):
        self.meeting_type = feed_options['meeting_type']
        super().__init__()

    def accepts(self, item):
        return True

class LocationFilter(DefaultAccept):
    def __init__(self, feed_options):
        self.meeting_type = feed_options['meeting_type']
        super().__init__(feed_options=feed_options)

    def accepts(self, item):
        if item['meeting_type'] != self.meeting_type:
            return False

        return super().accepts(item)
