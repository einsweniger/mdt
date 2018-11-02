from moodle.responses import MoodleGrade
from datetime import datetime

class Grade(MoodleGrade):
    @property
    def date_created(self): return datetime.fromtimestamp(self.time_created)

    @property
    def date_modified(self): return datetime.fromtimestamp(self.time_modified)

    @property
    def value(self):
        try:
            result = float(self.grade)
            if 0 > result:
                return None
            return result
        except ValueError:
            return None
