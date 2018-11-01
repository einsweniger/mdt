from .file import File
from moodle.models import MoodleFileArea
from typing import Iterable

class FileArea(MoodleFileArea):
    def __init__(self, data, submission):
        self.submission = submission
        super().__init__(data)
        self._files = [File(file, submission) for file in self.file_list.raw]

#        if Jn.files in self._data:
#            self.set_file_data(self.get(Jn.files))
        self.unparsed = data

    def __str__(self):
        out = self.area
        if self.has_content:
            out += ' has {:2d} files'.format(len(self._files))
        return out

    @property
    def has_content(self) -> bool:
        return len(self._files) > 0

    @property
    def files(self) -> Iterable[File]:
        yield from self._files

    def set_file_data(self, data):
        self._files = [File(file, self.submission) for file in data]

