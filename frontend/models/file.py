from moodle.responses import MoodleSubmissionFile
from moodle.parsers import file_meta_dict_from_url


class File(MoodleSubmissionFile):
    def __init__(self, data, submission):
        super().__init__(data)
        self.submission = submission
        self._new_path = None

    @property
    def path(self):
        if self._new_path is None:
            return self.file_path
        else:
            return self._new_path

    @path.setter
    def path(self, value):
        self._new_path = value

    @property
    def name(self): return self.file_name

    @property
    def size(self): return self.file_size

    @property
    def meta_data_params(self): return file_meta_dict_from_url(self.url)

