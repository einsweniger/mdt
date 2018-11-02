from moodle.responses import MoodleCourse
from .assignment import Assignment
from .user import User, Group

from typing import Dict


class Course(MoodleCourse):
    def __init__(self, data):
        super().__init__(data)
        self._users: Dict[int, User] = {}  # accessed via user.id
        self._groups: Dict[int, Group] = {}  # accessed via group.id
        self._assignments: Dict[int, Assignment] = {}

    @property
    def name(self) -> str:
        return self.fullname

    @property
    def users(self) -> Dict[int, User]:
        return self._users

    def parse_users(self, data):
        if data is None:
            self._users = {}
            return
        if 'errorcode' in data:
            return
        users = [User(u) for u in data]
        for user in users:
            self._users[user.id] = user
            self.parse_groups(user)

    @property
    def assignments(self) -> Dict[int, Assignment]:
        return self._assignments

    def parse_assignments(self, data):
        if data is None:
            self._assignments = {}
            return
        assignments = [Assignment(a, course=self) for a in data]
        for a in assignments:
            self._assignments[a.id] = a

    @property
    def groups(self) -> Dict[int, Group]:
        return self._groups

    def parse_groups(self, user: User):
        for group_id, group in user.groups.items():
            if group_id not in self._groups:
                self._groups[group_id] = group
            group = self._groups[group_id]
            group.members.append(user)

    def __str__(self):
        return f'{self.fullname[0:39]:40} id:{self.id:5d} short: {self.shortname}'

    def __repr__(self):
        return repr((self.fullname, self.id, self.shortname))

    def print_status(self):
        print(self)
        assignments = [a.short_status_string(indent=1) for a in self.assignments.values()]
        for a in sorted(assignments):
            print(a)

    def print_short_status(self):
        print(self)
        a_status = [a.short_status_string(indent=1) for a in self.assignments.values() if a.needs_grading]
        for a in sorted(a_status):
            print(a)

    def get_assignments(self, id_list):
        return [a for aid, a in self.assignments.items() if aid in id_list]
