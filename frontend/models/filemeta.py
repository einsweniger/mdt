from datetime import datetime

from moodle.responses import MoodleFileMeta


class FileMeta(MoodleFileMeta):
    @property
    def date_created(self): return datetime.fromtimestamp(self.time_created)

    @property
    def date_modified(self): return datetime.fromtimestamp(self.time_modified)
