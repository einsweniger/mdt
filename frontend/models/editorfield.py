from moodle.responses import MoodleEditorField


class EditorField(MoodleEditorField):
    def __str__(self):
        out = f'{self.name} {self.description}'
        if self.has_content:
            out += f' has text format {self.fmt:1d}'
        return out

    @property
    def has_content(self):
        return self.text.strip() != ''

    @property
    def content(self):
        return self.text

