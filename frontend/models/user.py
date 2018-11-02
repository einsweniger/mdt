from typing import Dict, List

from moodle.responses import MoodleUser, MoodleGroup


class Group(MoodleGroup):
    def __init__(self, data):
        super().__init__(data)
        self.members: List[User] = []

    def __str__(self):
        return f'{self.name:10} id:{self.id:5d} '


class User(MoodleUser):
    def __init__(self, data):
        super().__init__(data)
        self._groups = {}
        self.parse_groups(super().groups.raw)

    @property
    def name(self): return self.full_name

    @property
    def groups(self) -> Dict[int, Group]:
        return self._groups

    def parse_groups(self, data):
        for g in data:
            group = Group(g)
            self._groups[group.id] = group

    def __str__(self):
        return f'{self.name:20} id:{self.id:5d} groups:{self.groups}'
