from abc import abstractmethod, abstractproperty, ABC

from .file import File
from .plugin import Plugin
from .grade import Grade
from moodle.responses import MoodleSubmission
from util.werkzeug import cached_property
from typing import Dict, Tuple, Iterable, List


class SubmissionBase(MoodleSubmission, ABC):
    def __init__(self, data, assignment=None):
        super().__init__(data)
        self.assignment = assignment
        self._plugins = [Plugin(p, self) for p in self.plugin_list.raw]

    @property
    def plugins(self) -> Iterable[Plugin]:
        yield from self._plugins

    @cached_property
    def has_content(self) -> bool:
        return any([p.has_content for p in self.plugins])

    @property
    def has_files(self):
        for p in self._plugins:
            if p.has_file_content:
                return True
        return False

    def __str__(self):
        return 'id:{:7d} {:5d}:{:5d}'.format(self.id, self.user_id, self.group_id)

    @property
    def has_editor_field_content(self) -> bool:
        return any([p.has_editor_field_content for p in self._plugins])

    @property
    def editor_field_content(self) -> str:
        content = ''
        for p in self._plugins:
            if p.has_editor_field_content:
                content += p.editor_field_content
        return content

    @abstractmethod
    def status_string(self, indent=0) -> str:
        pass

    @property
    @abstractmethod
    def grade(self) -> Grade:
        pass

    @cached_property
    @abstractmethod
    def is_graded(self) -> bool:
        pass

    @property
    @abstractmethod
    def files(self) -> Iterable[File]:
        pass

    @property
    @abstractmethod
    def prefix(self) -> str:
        pass


class TeamSubmission(SubmissionBase):
    @property
    def prefix(self) -> str:
        try:
            group = self.assignment.course.groups[self.group_id]
            return group.name
        except KeyError:
            print(f'Assignment: {self.assignment}, group for submission: {self.id} has no members')
            return 'UNKNOWN_GROUP'

    @property
    def files(self) -> Iterable[File]:
        """
        returns all files of the submission.
        also has the problem with empty groups.
        team submissions that have no existing groups are discarded.
        assumption: argument `assignments` will contain the fully assembled data, so users and groups are populated.
        FIXME: submissions with empty groups.

        :return: the files if submission is valid.
        """
        if self.group_id not in self.assignment.course.groups:
            print(
                f'Assignment: {self.assignment}, group for submission: {self.id} has no members! \n will not download.')
            yield from []
        else:
            for p in self.plugins:
                yield from p.files

    def is_graded(self) -> bool:
        grade, warnings = self.get_grade_or_reason_if_team_ungraded()
        if grade is not None:
            return True
        else:
            return False

    @property
    def grade(self) -> Grade:
        grade, warnings = self.get_grade_or_reason_if_team_ungraded()
        return grade

    def get_grade_or_reason_if_team_ungraded(self):
        graded_users, ungraded_users = self.get_team_members_and_grades()
        grades = [grade for grade in graded_users.values()]
        grade_set = set([grade.value for grade in grades])
        set_size = len(grade_set)
        warnings = ''
        if len(graded_users) == 0:
            warnings += ' no grades'
        elif len(ungraded_users) > 1:
            warnings += ' has graded and ungraded users'
        if set_size > 1:
            warnings += ' grades not equal: ' + str(grade_set)
        if warnings == '':
            return grades.pop(), None
        else:
            return None, warnings

    def get_team_members_and_grades(self) -> Tuple[Dict[int, Grade], Dict[int,Grade]]:
        """
        When users switch groups and a group might not exist as a result thereof.
        This as such is not a problem.
        But, according to moodle's logic, a past submission is still connected to the group.
        As a result, accessing the group will fail, since no user is associated with it.
        To work around this, the local `members` variable is set to an empty list.
        TODO: think about a reasonable fix.
        TODO: inform user about discrepancy.
        """
        group = self.assignment.course.groups[self.group_id]
        try:
            members = group.members
        except KeyError:
            members = []

        grades = self.assignment.grades
        graded_users = {}
        ungraded_users = {}
        for user in members:
            if user.id in grades and grades[user.id].value is not None:
                graded_users[user.id] = grades[user.id]
            else:
                ungraded_users[user.id] = user

        return graded_users, ungraded_users

    def status_string(self, indent=0) -> str:
        if self.assignment is None:
            return ' ' * indent + str(self)

        if self.group_id not in self.assignment.course.groups:
            return ' ' * indent + str(self) + ' could not find group?'
        group = self.assignment.course.groups[self.group_id]

        grade, warnings = self.get_grade_or_reason_if_team_ungraded()
        grader = 'NAME UNKNOWN?'
        if grade is not None:
            if grade.grader_id in self.assignment.course.users:
                grader = self.assignment.course.users[grade.grader_id].name
            return ' ' * indent + '{:20} id:{:7d} grade:{:4} graded_by:{:10}'.format(group.name, self.id, grade.value,
                                                                                     grader)
        else:
            return ' ' * indent + '{:20} id:{:7d} WARNING:{}'.format(group.name, self.id, warnings)


class SingleSubmission(SubmissionBase):
    @property
    def files(self) -> Iterable[File]:
        for p in self.plugins:
            yield from p.files

    @property
    def prefix(self) -> str:
        user = self.assignment.course.users[self.user_id]
        return user.name

    def status_string(self, indent=0) -> str:
        if self.assignment is None:
            return ' ' * indent + str(self)

        user = self.assignment.course.users[self.user_id]
        if self.is_graded:
            grade = self.assignment.grades[self.user_id]
            grader = 'NAME UNKNOWN?'
            if grade.grader_id in self.assignment.course.users:
                grader = self.assignment.course.users[grade.grader_id].name
            return indent * ' ' + '{:20} grade:{:4} graded_by:{:10}'.format(user.name[0:19], grade.value, grader)
        else:
            return indent * ' ' + '{:20} ungraded'.format(user.name[0:19])

    @property
    def grade(self) -> Grade:
        return self.assignment.grades.get(self.user_id, None)

    def is_graded(self) -> bool:
        try:
            return self.assignment.grades[self.user_id].value is not None
        except KeyError:
            return False
