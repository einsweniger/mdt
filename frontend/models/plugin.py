from .editorfield import EditorField
from .filearea import FileArea
from .file import File
from moodle.responses import MoodlePlugin
from typing import Iterable


class Plugin(MoodlePlugin):
    def __init__(self, data, submission):
        super().__init__(data)
        self.submission = submission
        self._editor_fields = [EditorField(e) for e in self.editor_fields.raw]
        self._file_areas = [FileArea(a, submission) for a in self.file_areas.raw]

    def __str__(self):
        if self.has_content:
            out = ''
            plug = 'plugin:[{}] '
            if self.has_editor_field_content:
                out += plug.format('efield')
            if self.has_file_content:
                out += plug.format('files')
            return out
        else:
            return ''

    @property
    def has_editor_field_content(self) -> bool:
        return any([e.has_content for e in self._editor_fields])

    @property
    def has_file_content(self) -> bool:
        return any([f.has_content for f in self._file_areas])

    @property
    def has_content(self) -> bool:
        if self.has_editor_field_content or self.has_file_content:
            return True
        else:
            return False

    @property
    def files(self) -> Iterable[File]:
        for area in self._file_areas:
            yield from area.files

    @property
    def editor_field_content(self) -> str:
        content = ''
        if self.has_editor_field_content:
            for e in self._editor_fields:
                if e.has_content:
                    content += e.content
        return content

