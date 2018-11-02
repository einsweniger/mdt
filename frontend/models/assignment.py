from abc import ABC

from .file import File
from .submission import TeamSubmission, SingleSubmission, SubmissionBase
from .grade import Grade
from moodle.responses import MoodleAssignment
from datetime import datetime
from typing import Dict, Iterable


class AssignmentBase(MoodleAssignment, ABC):
    def __init__(self, data, course=None):
        super().__init__(data)
        self.course = course
        self._submissions = {}  # accessed via submission.id
        self._grades = {}  # are accessed via user_id

    @property
    def due_date(self) -> datetime:
        return datetime.fromtimestamp(super().duedate)

    @property
    def submissions(self) -> Dict[int, SubmissionBase]:
        return self._submissions

    @property
    def grades(self) -> Dict[int, Grade]:
        return self._grades

    @property
    def valid_submission_count(self) -> int:
        return len(list(self.valid_submissions))

    @property
    def valid_submissions(self) -> Iterable[SubmissionBase]:
        for sub in self.submissions.values():
            if sub.has_content:
                yield sub

    @property
    def files(self) -> Iterable[File]:
        for submission in self.submissions.values():
            yield from submission.files


    @property
    def is_due(self) -> bool:
        now = datetime.now()
        diff = now - self.due_date
        ignore_older_than = 25 * 7  # 25 weeks is approx. half a year.
        return now > self.due_date and diff.days < ignore_older_than

    @property
    def grade_count(self) -> int:
        return len(self.grades)


    def parse_submissions(self, data: list):
        if data is None:
            self._submissions = {}
            return
        for submission in data:
            if self.teamsubmission:
                sub = TeamSubmission(submission, assignment=self)
            else:
                sub = SingleSubmission(submission, assignment=self)
            if sub.has_content:
                self._submissions[sub.id] = sub

    def parse_grades(self, data):
        if data is None:
            self._grades = {}
            return
        for grade_data in data:
            grade = Grade(grade_data)
            self._grades[grade.user_id] = grade

    def __str__(self):
        return f'{self.name[0:39]:40} id:{self.id:5d}'



class Assignment(AssignmentBase):
    def __init__(self, data, course=None):
        super().__init__(data)
        self.course = course
        self._submissions = {}  # accessed via submission.id
        self._grades = {}  # are accessed via user_id

    @property
    def grading_file_content(self):
        # TODO, instead of writing the submission.id, write the user.id instead.
        # TODO, add team_submission to the file, saves work when uploading grades.
        head = '{{"assignment_id": {:d}, "grades": [\n'
        end = '\n]}'
        line_format = '{{"name": "{}", "id": {:d}, "grade": {:3.1f}, "feedback":"" }}'
        content = []

        if self.teamsubmission:
            for s_id, s in self.submissions.items():
                if s.groupid not in self.course.groups:
                    # FIXME: invalid grouping
                    continue
                group = self.course.groups[s.groupid]
                grade = 0.0
                if s.grade is not None:
                    grade = s.grade.value or 0.0

                line = f'{{"name": "{group.name}", "id": {s.id}, "grade": {grade:3.1f}, "feedback":"" }}'
                content.append(line)
        else:
            for s_id, s in self.submissions.items():
                user = self.course.users[s.userid]
                grade = 0.0
                if s.grade is not None:
                    grade = s.grade.value or 0.0
                print(f'{user.name}')
                print(f'{s.id}')
                print(f'{grade}')
                line = f'{{"name": "{user.name}", "id": {s.id}, "grade": {grade:3.1f}, "feedback":"" }}'
                content.append(line)

        return head.format(self.id) + ',\n'.join(sorted(content)) + end

    @property
    def needs_grading(self) -> bool:
        all_graded = all([s.is_graded for s in self.valid_submissions])
        return self.is_due and not all_graded

    def short_status_string(self, indent=0):
        fmt_string = ' ' * indent + str(self) + f' submissions:{self.valid_submission_count:3d}'
        fmt_string += f' due:{self.is_due:1} graded:{not self.needs_grading:1}'
        return fmt_string

    def detailed_status_string(self, indent=0):
        string = ' ' * indent + str(self) + '\n'
        string += self.config_status_string(indent=indent+1)
        s_status = [s.status_string(indent=indent + 1) for s in self.valid_submissions]
        string += '\n'.join(sorted(s_status))
        return string

    def config_status_string(self, indent=0):
        _configs = {}
        for config in self.configurations:
            if config.sub_type not in _configs:
                _configs[config.sub_type] = {config.plugin: {config.name: config.value}}
            elif config.plugin not in _configs[config.sub_type]:
                _configs[config.sub_type][config.plugin] = {config.name: config.value}
            else:
                _configs[config.sub_type][config.plugin][config.name] = config.value

        string = ''
        for sub_type, config_list in _configs.items():
            string += ' ' * indent + 'cfg-' + sub_type + ': '
            s_config = [plugin+'='+str(config) for plugin, config in config_list.items()]
            string += ', '.join(sorted(s_config))
            string += '\n'
        return string

    @property
    def merged_html(self):
        # TODO use mathjax local, not remote cdn. maybe on init or auth?
        # html = ''
        html = '<head><meta charset="UTF-8"></head><body>' \
               '<script src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>'
        seperator_single = '\n\n\n<h1>{}</h1>\n\n\n'
        seperator_team = '\n\n\n<h1>{} - {}</h1>\n\n\n'
        assembled_tmp = []
        for s in self.valid_submissions:
            tmp = ''
            if s.has_editor_field_content and s.editor_field_content.strip() != '':
                if self.teamsubmission:
                    group = self.course.groups[s.group_id]
                    member_names = [user.name for user in group.members]
                    tmp += seperator_team.format(group.name, ', '.join(member_names))
                else:
                    user = self.course.users[s.user_id]
                    tmp += seperator_single.format(user.name)
                tmp += s.editor_field_content
                assembled_tmp.append(tmp)

        if len(assembled_tmp) == 0:
            return None

        html += ''.join(sorted(assembled_tmp))
        return html + '</body>'


