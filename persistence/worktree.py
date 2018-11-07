import glob
import json
import os
import re

from pathlib import Path

from moodle import responses
from moodle.fieldnames import JsonFieldNames as Jn
from moodle.responses import MoodleAssignment
from persistence.models import AssignmentFolder, SubmissionFolder, GradeFolder, MappedDataclassFolder
from util import zipwrangler
from typing import List, Iterable
from enum import Enum

__all__ = ['WorkTree', 'NotInWorkTree']


def _load_json_file(path: Path):
    try:
        with path.open('r') as file:
            return json.load(file)
    except json.decoder.JSONDecodeError as e:
        print(e)
        pass


class FolderNames(Enum):
    META_DATA_FOLDER = '.mdt'
    LOCAL_CONFIG = 'config'
    USERS = 'users'
    COURSES = 'courses'
    SYNC = 'sync'
    MOODLE = 'moodle'


class MdtConfig:
    def __init__(self):
        self.config = self.data_root / FolderNames.LOCAL_CONFIG.value

    @staticmethod
    def get_config_values():
        file_names = MdtConfig.get_config_file_list()
        global_config = MdtConfig.get_global_config_values()
        for name in file_names:
            with name.open('r') as file:
                try:
                    values = json.load(file)
                    global_config.add_overrides(values)
                except json.decoder.JSONDecodeError:
                    # probably old-style ini config
                    pass
        return global_config


    @classmethod
    def get_config_file_list(cls):
        global_config = cls.get_global_config_filename()
        cfg_files = [global_config]
        work_tree = WorkTree.find_work_tree_root()
        if work_tree is not None:
            # default_config_files order is crucial: work_tree cfg overrides global
            cfg_files.append(work_tree / FolderNames.META_DATA_FOLDER.value / FolderNames.LOCAL_CONFIG.value)
        return cfg_files

    @staticmethod
    def write_global_config(config_dict):
        WorkTree._write_data(MdtConfig.get_global_config_filename(), config_dict)

    def write_local_config(self, config_data):
        WorkTree._write_data(self.config, config_data)


    @staticmethod
    def get_local_config_file():
        work_tree = WorkTree.find_work_tree_root()

        if work_tree is None:
            return None

        config = work_tree / FolderNames.META_DATA_FOLDER.value / FolderNames.LOCAL_CONFIG.value
        if not config.is_file():
            return None

        return config


class MetaDataStorage:
    def __init__(self, root: Path, init: bool = False):
        self.data_root = root / FolderNames.META_DATA_FOLDER.value
        self.user_data = self.data_root / FolderNames.USERS.value
        self.sync_data = self.data_root / FolderNames.SYNC.value
        self.moodle_data = self.data_root / FolderNames.MOODLE.value
        self.course_data = self.data_root / FolderNames.COURSES.value
        self._course_data = _load_json_file(self.course_data)
        self._user_data = MappedDataclassFolder(self.data_root/'users', responses.MoodleUser)
        self._assignment_data = AssignmentFolder(self.data_root, init)
        self._submission_data = SubmissionFolder(self.data_root, init)
        self._grade_data = GradeFolder(self.data_root, init)

    @staticmethod
    def _write_config(path, data):
        with open(path, 'w') as file:
            file.write(data)

    @staticmethod
    def _write_data(path, data):
        with open(path, 'w') as file:
            json.dump(data, file, indent=2, ensure_ascii=False, sort_keys=True)

    @property
    def assignments(self):
        return self._assignment_data

    @property
    def submissions(self):
        return self._submission_data

    @property
    def courses(self):
        courses = {}
        for course in self._course_data:
            courses[course['id']] = course
        return courses

    def write_course_data(self, value):
        self._write_data(self.course_data, value)
        self._course_data = value

    @property
    def grades(self):
        return self._grade_data

    @property
    def users(self):
        return self._user_data

    def write_user_data(self, value):
        self._write_data(self.user_data, value)
        self._user_data = value


def safe_file_name(name):
    return re.sub(r'\W', '_', name)


class WorkTree:
    def __init__(self, init=False, skip_init=False):
        if skip_init:
            return

        self.root = self.find_work_tree_root()
        if self.root is None:
            if not init:
                raise NotInWorkTree()

        if init:
            self.root = self._initialize()

        self.meta = MetaDataStorage(self.root, init)


    def get_folder_for_assignment(self, assignment_id) -> Path:
        assignment = MoodleAssignment(**self.meta.assignments[assignment_id])
        prefix = safe_file_name(assignment.name)
        folder_name = f'{prefix}--{assignment_id:d}'
        path = self.root / folder_name
        if not path.is_dir():
            path.mkdir()
        return path


    @classmethod
    def _initialize(cls):
        root = Path.cwd() / FolderNames.META_DATA_FOLDER.value
        root.mkdir(exist_ok=True)
        users = root / FolderNames.USERS.value
        courses = root / FolderNames.COURSES.value
        if not courses.is_file():
            courses.write_text('[]')
        return Path.cwd()


    @classmethod
    def find_work_tree_root(cls):
        """
        determines the work tree root by looking at the .mdt folder in cwd or parent folders

        :returns the work tree root as Path or None
        """
        cwd = Path.cwd()
        if (cwd / FolderNames.META_DATA_FOLDER.value).is_dir():
            return cwd
        for parent in cwd.parents:
            if (parent / FolderNames.META_DATA_FOLDER.value).is_dir():
                return parent
        else:
            return None

    @property
    def in_root(self):
        return (Path.cwd() / FolderNames.META_DATA_FOLDER.value).is_dir()

    @property
    def in_tree(self):
        return self.find_work_tree_root() is not None

    # @property
    # def data(self):
    #     cs = []
    #
    #     for course_data in self.meta.courses.values():
    #         course = Course(course_data)
    #         users = self.meta.users
    #         if users is None or len(users) == 0:
    #             no_users_msg = """
    #             No users in courses found.
    #             If you did not sync already, metadata is probably missing.
    #             Use subcommand fetch to retrieve metadata from selected moodle
    #             courses.
    #             """
    #             raise SystemExit(no_users_msg)
    #         else:
    #             course.parse_users(users[str(course.id)])
    #
    #         assignment_list = []
    #         for assignment_data in self.meta.assignments.values():
    #             if assignment_data[Jn.course] == course.id:
    #                 assignment_list.append(assignment_data)
    #         # course.assignments = [a for a in self.assignments.values() if a[Jn.course] == course.id]
    #         course.parse_assignments(assignment_list)
    #
    #         for assignment in course.assignments.values():
    #             assignment.parse_submissions(self.meta.submissions.get(assignment.id, None))
    #             assignment.parse_grades(self.meta.grades.get(assignment.id, None))
    #
    #         cs.append(course)
    #     return cs

    def _merge_json_data_in_folder(self, path):
        files = glob.glob(path + '*')
        data_list = [_load_json_file(file) for file in files]
        return data_list

    def write_grading_and_html_file(self, assignment):
        # TODO: check if submission was after deadline and write to grading file
        a_folder = self.root / self.formatted_assignment_folder(assignment)
        grade_file = a_folder / 'gradingfile.json'
        if grade_file.is_file():
            counter = 0
            grade_file = a_folder / f'gradingfile_{counter:02d}.json'
            while grade_file.is_file():
                counter += 1
                grade_file = a_folder / f'gradingfile_{counter:02d}.json'
            print(f'grading file exists, writing to: {grade_file}')
        a_folder.mkdir(exist_ok=True)

        grade_file.write_text(assignment.grading_file_content)

        html_content = assignment.merged_html
        if html_content is not None:
            html_file = a_folder / '00_merged_submissions.html'
            html_file.write_text(html_content)

class NotInWorkTree(Exception):
    def __init__(self):
        self.message = 'You are not in an initialized work tree. Go get one.'

    def __str__(self):
        return self.message
