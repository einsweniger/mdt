from moodle.responses import JsonDictWrapper, JsonListWrapper
from typing import Iterable


class Grade(JsonDictWrapper):
    @property
    def name(self):
        return self['name']

    @property
    def id(self):
        return self['id']

    @id.setter
    def id(self, value):
        self._data['id'] = value

    @property
    def grade(self):
        return self['grade']

    @property
    def feedback(self):
        return self['feedback']


class GradeList(JsonListWrapper):
    def __iter__(self) -> Iterable[Grade]:
        for grade in self._data:
            yield Grade(grade)


class GradingFile(JsonDictWrapper):
    @property
    def assignment_id(self) -> int:
        return self['assignment_id']

    @property
    def team_submission(self) -> bool:
        return self.get('team_submission', False)

    @team_submission.setter
    def team_submission(self, value: bool):
        self._data['team_submission'] = value

    @property
    def grades(self) -> GradeList:
        return GradeList(self['grades'])

