import inspect
from abc import abstractmethod
from collections import Mapping, Sequence, Sized, namedtuple as nt
from dataclasses import dataclass
import dataclasses as dc
from typing import List, Any, Union, Sequence, Optional
import collections
from datetime import datetime
import typing
from moodle.fieldnames import JsonFieldNames as Jn
import logging


DEBUG = True
log = logging.getLogger('moodle.responses')
T = typing.TypeVar('T')


def destructuring_list_cast(cls: typing.Callable[[dict], T]) -> typing.Callable[[list], T]:
    def cast(data: list) -> List[T]:
        if data is None:
            return []

        if not isinstance(data, list):
            raise TypeError(f'listcast expects a list, you sent: {type(data)}')
        try:
            return [cls(**entry) for entry in data]
        except TypeError as err:
            provided = set()
            for x in data:
                provided.update(set(x.keys()))
            expected = set(inspect.signature(cls).parameters.keys())
            print(f'provided data has keys:')
            for p in sorted(provided):
                print(f'  {p}')
            print(f'callable expects:')
            for e in sorted(expected):
                print(f'  {e}')
            print(f'difference expected -> proided:')
            for pe in sorted(expected.difference(provided)):
                print(f'    {pe}')
            print(f'difference proided -> expected:')
            for ep in provided.difference(expected):
                print(f'    {ep}')

            raise NotImplementedError(f'listcast for class {cls} failed:\n{err}')
    return cast

# destructured_cast_field
def dcf(cls):
    return dc.field(metadata={'castfunc': destructuring_list_cast(cls)})

def optional_dcf(cls):
    return dc.field(metadata={'castfunc': destructuring_list_cast(cls)}, default=None)

@dataclass
class BaseDC:
    def _typecheck(self):
        for field in dc.fields(self):
            expected = field.type
            f = getattr(self, field.name)
            actual = type(f)
            if expected is list or expected is dict:
                log.warning(f'untyped list or dict in {self.__class__.__qualname__}: {field.name}')
            if expected is actual:
                continue
            if expected.__class__ is typing._GenericAlias:
                return self._typecheck_generic(expected, actual)
                # Subscripted generics cannot be used with class and instance checks
            if issubclass(actual, expected):
                continue
            print(f'mismatch {field.name}: should be: {expected}, but is {actual}')
            print(f'offending value: {f}')

    def __post_init__(self):
        for field in dc.fields(self):
            castfunc = field.metadata.get('castfunc', False)
            if castfunc:
                attr = getattr(self, field.name)
                new = castfunc(attr)
                setattr(self, field.name, new)
        if DEBUG:
            self._typecheck()

    def _typecheck_generic(self, expected, actual):
        assert '__origin__' in expected.__dict__
        if expected.__origin__ is typing.Union:
            for arg in expected.__args__:
                if actual is arg:
                    break
            else:
                print(f'specified Union {expected} does not contain {actual}')
            return
        if expected.__origin__ is list:
            #print(f'idunno, List expected: {expected} is {actual}')
            #print(dir(actual))
            return
        raise RuntimeError('this was an unexpected generic')


@dataclass
class DCcore_enrol_get_users_courses(BaseDC):
    id: int   #id of course
    shortname: str   #short name of course
    fullname: str   #long name of course
    enrolledusercount: int   #Number of enrolled users in this course
    idnumber: str   #id number of course
    visible: int   #1 means visible, 0 means hidden course
    summary: Optional[str] = None  #summary
    summaryformat: Optional[int] = None  #summary format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
    format: Optional[str] = None  #course format: weeks, topics, social, site
    showgrades: Optional[int] = None  #true if grades are shown, otherwise false
    lang: Optional[str] = None  #forced course language
    enablecompletion: Optional[int] = None  #true if completion is enabled, otherwise false
    category: Optional[int] = None  #course category id
    progress: Optional[float] = None  #Progress percentage
    startdate: Optional[int] = None  #Timestamp when the course start
    enddate: Optional[int] = None  #Timestamp when the course end

    def __str__(self): return f'{self.fullname[0:39]:40} id:{self.id:5d} short: {self.shortname}'

core_enrol_get_users_courses = destructuring_list_cast(DCcore_enrol_get_users_courses)

@dataclass
class DCcore_enrol_get_enrolled_users(BaseDC):
    @dataclass
    class customfield(BaseDC):
        type: str   #The type of the custom field - text field, checkbox...
        value: str   #The value of the custom field
        name: str   #The name of the custom field
        shortname: str   #The shortname of the custom field - to be able to build the field class in the code
    @dataclass
    class group(BaseDC):
        id: int   #group id
        name: str   #group name
        description: str   #group description
        descriptionformat: int   #description format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
    @dataclass
    class role(BaseDC):
        roleid: int   #role id
        name: str   #role name
        shortname: str   #role shortname
        sortorder: int   #role sortorder
    @dataclass
    class preference(BaseDC):
        name: str   #The name of the preferences
        value: str   #The value of the custom field
    @dataclass
    class enrolledcourse(BaseDC):
        id: int   #Id of the course
        fullname: str   #Fullname of the course
        shortname: str   #Shortname of the course
    id: int   #ID of the user
    fullname: str   #The fullname of the user

    customfields:     Optional[List[customfield]]    = optional_dcf(customfield)  # User custom fields (also known as user profil fields)
    groups:           Optional[List[group]]          = optional_dcf(group)  # user groups
    roles:            Optional[List[role]]           = optional_dcf(role)  # user roles
    preferences:      Optional[List[preference]]     = optional_dcf(preference)  # User preferences
    enrolledcourses:  Optional[List[enrolledcourse]] = optional_dcf(enrolledcourse)  # Courses where the user is enrolled - limited by which courses the user is able to see

    username: Optional[str] = None  #Username policy is defined in Moodle security config
    firstname: Optional[str] = None  #The first name(s) of the user
    lastname: Optional[str] = None  #The family name of the user
    email: Optional[str] = None  #An email address - allow email as root@localhost
    address: Optional[str] = None  #Postal address
    phone1: Optional[str] = None  #Phone 1
    phone2: Optional[str] = None  #Phone 2
    icq: Optional[str] = None  #icq number
    skype: Optional[str] = None  #skype id
    yahoo: Optional[str] = None  #yahoo id
    aim: Optional[str] = None  #aim id
    msn: Optional[str] = None  #msn number
    department: Optional[str] = None  #department
    institution: Optional[str] = None  #institution
    idnumber: Optional[str] = None  #An arbitrary ID code number perhaps from the institution
    interests: Optional[str] = None  #user interests (separated by commas)
    firstaccess: Optional[int] = None  #first access to the site (0 if never)
    lastaccess: Optional[int] = None  #last access to the site (0 if never)
    description: Optional[str] = None  #User profile description
    descriptionformat: Optional[int] = None  #description format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
    city: Optional[str] = None  #Home city of the user
    url: Optional[str] = None  #URL of the user
    country: Optional[str] = None  #Home country code of the user, such as AU or CZ
    profileimageurlsmall: Optional[str] = None  #User image profile URL - small version
    profileimageurl: Optional[str] = None  #User image profile URL - big version


core_enrol_get_enrolled_users = destructuring_list_cast(DCcore_enrol_get_enrolled_users)

@dataclass
class mod_assign_get_assignments(BaseDC):
    @dataclass  # course information object
    class course(BaseDC):
        @dataclass
        class assignment(BaseDC):
            id: int  # assignment id
            cmid: int  # course module id
            course: int  # course id
            name: str   # assignment name
            nosubmissions: int  # no submissions
            submissiondrafts: int  # submissions drafts
            sendnotifications: int  # send notifications
            sendlatenotifications: int  # send notifications
            sendstudentnotifications: int  # send student notifications (default)
            duedate: int  # assignment due date
            allowsubmissionsfromdate: int  # allow submissions from date
            grade: int  # grade type
            timemodified: int  # last time assignment was modified
            completionsubmit: int  # if enabled, set activity as complete following submission
            cutoffdate: int  # date after which submission is not accepted without an extension
            gradingduedate: int  # the expected date for marking the submissions
            teamsubmission: int  # if enabled, students submit as a team
            requireallteammemberssubmit: int  # if enabled, all team members must submit
            teamsubmissiongroupingid: int  # the grouping id for the team submission groups
            blindmarking: int  # if enabled, hide identities until reveal identities actioned
            revealidentities: int  # show identities for a blind marking assignment
            attemptreopenmethod: str   # method used to control opening new attempts
            maxattempts: int  # maximum number of attempts allowed
            markingworkflow: int  # enable marking workflow
            markingallocation: int  # enable marking allocation
            requiresubmissionstatement: int  # student must accept submission statement
            @dataclass
            class config(BaseDC): # assignment configuration object
                plugin: str   # plugin
                subtype: str   # subtype
                name: str   # name
                value: str   # value
                id: Optional[int] = None # assign_plugin_config id
                assignment: Optional[int] = None # assignment id
            @dataclass
            class introfile(BaseDC): # File.
                filename: Optional[str] = None # File name.
                filepath: Optional[str] = None # File path.
                filesize: Optional[int] = None # File size.
                fileurl: Optional[str] = None # Downloadable file url.
                timemodified: Optional[int] = None # Time modified.
                mimetype: Optional[str] = None # File mime type.
                isexternalfile: Optional[int] = None # Whether is an external file.
                repositorytype: Optional[str] = None # The repository type for external files.
            @dataclass
            class introattachment(BaseDC):  # File.
                filename: Optional[str] = None # File name.
                filepath: Optional[str] = None # File path.
                filesize: Optional[int] = None # File size.
                fileurl: Optional[str] = None # Downloadable file url.
                timemodified: Optional[int] = None # Time modified.
                mimetype: Optional[str] = None # File mime type.
                isexternalfile: Optional[int] = None # Whether is an external file.
                repositorytype: Optional[str] = None # The repository type for external files.

            configs:          List[config] = dcf(config) # configuration settings
            introfiles:       Optional[List[introfile]] = dcf(introfile) # Files in the introduction text
            introattachments: Optional[List[introattachment]] = dcf(introattachment) # intro attachments files

            preventsubmissionnotingroup: Optional[int] = None # Prevent submission not in group
            submissionstatement: Optional[str] = None # Submission statement formatted.
            submissionstatementformat: Optional[int] = None # submissionstatement format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
            intro: Optional[str] = None # assignment intro, not allways returned because it deppends on the activity configuration
            introformat: Optional[int] = None # intro format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
        id: int  # course id
        fullname: str   # course full name
        shortname: str   # course short name
        timemodified: int  # last time modified
        assignments: List[assignment] = dcf(assignment)# assignment info # list of ( object {  # assignment information object
    @dataclass
    class warning(BaseDC):
        warningcode: str   # errorcode can be 1 (no access rights) or 2 (not enrolled or no permissions)
        message: str   # untranslated english message to explain the warning
        itemid: Optional[int] = None # When item is a course then itemid is a course id. When the item is a module then itemid is a module id
        item: Optional[str] = None # item can be 'course' (errorcode 1 or 2) or 'module' (errorcode 1)
    courses: List[course] = dcf(course)  # list of courses
    warnings: Optional[List[warning]] = dcf(warning) # list of warnings

@dataclass
class mod_assign_get_submissions(BaseDC):
    @dataclass
    class warning(BaseDC):
        warningcode: str  #the warning code can be used by the client app to implement specific behaviour
        message: str  #untranslated english message to explain the warning
        item: Optional[str] = None  #item
        itemid: Optional[int] = None  #item id
    @dataclass
    class assignment(BaseDC):
        @dataclass
        class submission(BaseDC):
            id: int  #submission id
            userid: int  #student id
            attemptnumber: int  #attempt number
            timecreated: int  #submission creation time
            timemodified: int  #submission last modified time
            status: str  #submission status
            groupid: int  #group id
            @dataclass
            class plugin(BaseDC):
                type: str  #submission plugin type
                name: str  #submission plugin name
                @dataclass
                class editorfield(BaseDC):
                    name: str  #field name
                    description: str  #field description
                    text: str  #field value
                    format: int  #text format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
                @dataclass
                class filearea(BaseDC):
                    area: str  #file area
                    files : Optional[list]  #files
                    @dataclass
                    class file(BaseDC):
                        filename: Optional[str] = None  #File name.
                        filepath: Optional[str] = None  #File path.
                        filesize: Optional[int] = None  #File size.
                        fileurl: Optional[str] = None  #Downloadable file url.
                        timemodified: Optional[int] = None  #Time modified.
                        mimetype: Optional[str] = None  #File mime type.
                        isexternalfile: Optional[int] = None  #Whether is an external file.
                        repositorytype: Optional[str] = None  #The repository type for external files.
                editorfields : Optional[List[editorfield]] = optional_dcf(editorfield) #editorfields
                fileareas:     Optional[List[filearea]]    = optional_dcf(filearea) #fileareas

            plugins: Optional[List[plugin]] = dcf(plugin)  #plugins
            assignment: Optional[int] = None  #assignment id
            latest: Optional[int] = None  #latest attempt

            gradingstatus: Optional[str] = None  #Grading status.
        assignmentid: int  #assignment id
        submissions: List[submission] = dcf(submission)#submission info
    assignments: List[assignment] = dcf(assignment) #assignment submissions
    warnings : Optional[List[warning]] = optional_dcf(warning) #list of warnings


class JsonWrapper(Sized):
    def __len__(self):
        return len(self._data)

    def __init__(self, json):
        self._data = json

    @property
    def raw(self): return self._data


class JsonListWrapper(JsonWrapper, Sequence):
    def __getitem__(self, index):
        return self._data[index]

    def __init__(self, json_list):
        if not issubclass(type(json_list), Sequence):
            raise TypeError(f'received type {type(json_list)}, expected Sequence')
        super().__init__(json_list)
        if DEBUG:
            list(self)

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError('__iter__')

    def get(self, index):
        try:
            return self._data[index]
        except Exception as e:
            print(index)
            raise e


class JsonDictWrapper(JsonWrapper, Mapping):
    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        """
            Search for key.
            KeyError will be thrown, if the key cannot be found.
        """
        try:
            return self._data[key]
        except KeyError:
            raise

    def __init__(self, json_dict):
        if not issubclass(type(json_dict), Mapping):
            raise TypeError(f'received type {type(json_dict)}, expected Mapping')
        super().__init__(json_dict)

    _marker = object()

    def get(self, key, default=_marker):
        try:
            return self._data[key]
        except KeyError:
            if default is self._marker:
                raise
            else:
                return default

mod_assign_get_grades
class AssignmentGradeResponse(JsonDictWrapper):
    def print_warnings(self):
        for warning in self.warnings:
            if warning.warning_code == "3":
                # grades empty, no warning necessary
                pass
            elif warning.warning_code == "1":
                log.warning(f'{warning.item_id:5d}: {warning.message}')

    @property
    def assignments(self): return self.AssignmentList(self[Jn.assignments])

    @property
    def warnings(self): return self.WarningList(self.get(Jn.warnings, []))

    class AssignmentList(JsonListWrapper):

        def __iter__(self):
            for assignment in self._data:
                yield self.Assignment(assignment)

        class Assignment(JsonDictWrapper):
            @property
            def id(self): return self[Jn.assignment_id]

            @property
            def grades(self): return self.GradesList(self[Jn.grades])

            class GradesList(JsonListWrapper):
                def __iter__(self):
                    for grade in self._data:
                        yield self.Grade(grade)

                class Grade(JsonDictWrapper):
                    @property
                    def id(self): return self[Jn.id]

                    @property  #: str!
                    def grade(self): return self[Jn.grade]

                    @property
                    def grader_id(self): return self[Jn.grader]

                    @property
                    def user_id(self): return self[Jn.user_id]

                    @property
                    def attempt_number(self): return self[Jn.attempt_number]

                    @property
                    def time_created(self): return self[Jn.time_created]

                    @property
                    def time_modified(self): return self[Jn.time_modified]

                    @property
                    def assignment(self): return self.get(Jn.assignment, -1)

    class WarningList(JsonListWrapper):
        def __iter__(self):
            for warning in self._data:
                yield self.Warning(warning)

        class Warning(JsonDictWrapper):
            """
            item: str #Optional //item is always 'assignment'
            itemid int #Optional //when errorcode is 3 then itemid is an assignment id.
                        When errorcode is 1, itemid is a course module id
            warningcode: str   //errorcode can be 3 (no grades found) or 1 (no permission to get grades)
            message: str   //untranslated english message to explain the warning"""

            @property
            def warning_code(self): return self[Jn.warning_code]

            @property
            def message(self): return self[Jn.message]

            @property
            def item_id(self): return self.get(Jn.item_id, -1)

            @property
            def item(self): return self.get(Jn.item, '')

core_files_get_files
class FileMetaDataResponse(JsonDictWrapper):
    @property
    def parents(self): return self.ParentList(self[Jn.parents])

    @property
    def files(self): return self.FileList(self[Jn.files])

    class ParentList(JsonListWrapper):
        def __iter__(self):
            for parent in self._data:
                yield self.Parent(parent)

        class Parent(JsonDictWrapper):
            @property
            def context_id(self): return self[Jn.context_id]

            @property
            def component(self): return self[Jn.component]

            @property
            def file_area(self): return self[Jn.file_area]

            @property
            def item_id(self): return self[Jn.item_id]

            @property
            def file_path(self): return self[Jn.file_path]

            @property
            def filename(self): return self[Jn.file_name]

    class FileList(JsonListWrapper):
        def __iter__(self):
            for file in self._data:
                yield self.File(file)

        class File(JsonDictWrapper):
            @property
            def context_id(self): return self[Jn.context_id]

            @property
            def component(self): return self[Jn.component]

            @property
            def file_area(self): return self[Jn.file_area]

            @property
            def item_id(self): return self[Jn.item_id]

            @property
            def file_path(self): return self[Jn.file_path]

            @property
            def filename(self): return self[Jn.file_name]

            @property
            def isdir(self): return 1 == self[Jn.is_dir]

            @property
            def url(self): return self[Jn.url]

            @property
            def time_modified(self): return self[Jn.time_modified]

            @property
            def time_created(self): return self.get(Jn.time_created, 0)

            @property
            def file_size(self): return self.get(Jn.file_size, -1)

            @property
            def author(self): return self.get(Jn.author, "")

            @property
            def license(self): return self.get(Jn.license, "")

core_course_get_contents
class CourseContentResponse(JsonListWrapper):
    def __iter__(self):
        for section in self._data:
            yield self.CourseSection(section)

    class CourseSection(JsonDictWrapper):
        @property
        def id(self): return self[Jn.id]

        @property
        def name(self): return self[Jn.name]

        @property
        def visible(self): return self.get(Jn.visible, -1)

        @property
        def summary(self): return self[Jn.summary]

        @property
        def summary_format(self): return self[Jn.summary_format]

        @property
        def modules(self): return self.ModuleList(self[Jn.modules])

        class ModuleList(JsonListWrapper):
            def __iter__(self):
                for module in self._data:
                    yield self.Module(module)

            class Module(JsonDictWrapper):
                """ unimplemented, moodle calls these activity.
                url: str #Optional //activity url
                instance int #Optional //instance id
                description: str #Optional //activity description
                visible int #Optional //is the module visible
                availability: str #Optional //module availability settings
                """
                @property
                def id(self): return self[Jn.id]

                @property
                def instance(self):
                    """ the instance id """
                    return self.get(Jn.instance, -1)

                @property
                def name(self): return self[Jn.name]

                @property
                def modname(self):
                    """activity module type"""
                    return self[Jn.modname]

                @property
                def modicon(self): return self[Jn.modicon]

                @property
                def modplural(self): return self[Jn.modplural]

                @property
                def indent(self): return self[Jn.indent]

                @property
                def contents(self):
                    """is not marked as#Optional, but is only in modname == 'folder'"""
                    return self.ContentList(self.get(Jn.contents, []))

                class ContentList(JsonListWrapper):
                    def __iter__(self):
                        for content in self._data:
                            yield self.Content(content)

                    class Content(JsonDictWrapper):
                        """
                        fileurl: str #Optional //downloadable file url
                        content: str #Optional //Raw content, will be used when type is content
                        """
                        @property
                        def type(self): return self[Jn.type]

                        @property
                        def filename(self): return self[Jn.file_name]

                        @property
                        def file_path(self): return self[Jn.file_path]

                        @property
                        def file_size(self): return self[Jn.file_size]

                        @property
                        def time_modified(self): return self[Jn.time_modified]

                        @property
                        def time_created(self): return self[Jn.time_created]

                        @property
                        def author(self): return self[Jn.author]

                        @property
                        def license(self): return self[Jn.license]

                        @property
                        def user_id(self): return self[Jn.user_id]

                        @property
                        def sort_order(self): return 1 == self[Jn.sort_order]

                        @property
                        def url(self): return self[Jn.url]

welp  # used in session.upload_files
class FileUploadResponse(JsonListWrapper):
    def __iter__(self):
        for file in self._data:
            yield self.FileResponse(file)

    def __init__(self, json_list):
        super().__init__(json_list)
        self._errors = []
        for item in json_list:
            if 'error' in item:
                self._data.remove(item)
                self._errors.append(item)

    @property
    def has_errors(self):
        return len(self._errors) > 0

    @property
    def errors(self):
        return self.ErrorList(self._errors)

    class FileResponse(JsonDictWrapper):
        """ unimplemented:
        "component":"user",
        "contextid":1591,
        "userid":"358",
        "filearea":"draft",
        "filename":"hurr.pdf",
        "filepath":"\/",
        "itemid":528004240,
        "license":"allrightsreserved",
        "author":"rawr",
        "source":""
        """
        @property
        def item_id(self): return self['itemid']

    class ErrorList(JsonListWrapper):
        def __iter__(self):
            for error in self._data:
                yield self.Error(error)

        class Error(JsonDictWrapper):
            def __str__(self):
                return f'file: {self.file_name}, path: {self.file_path}, type {self.error_type}, error {self.error}'

            @property
            def file_name(self): return self['filename']

            @property
            def file_path(self): return self['filepath']

            @property
            def error_type(self): return self['errortype']

            @property
            def error(self): return self['error']


MoodleCourse = DCcore_enrol_get_users_courses
MoodleUser = DCcore_enrol_get_enrolled_users
MoodleGroup = DCcore_enrol_get_enrolled_users.group

MoodleAssignment = mod_assign_get_assignments.course.assignment

MoodleSubmissionList = destructuring_list_cast(mod_assign_get_submissions.assignment.submission)
MoodleSubmission = mod_assign_get_submissions.assignment.submission
MoodlePlugin = mod_assign_get_submissions.assignment.submission.plugin
MoodleFileArea = mod_assign_get_submissions.assignment.submission.plugin.filearea
MoodleEditorField = mod_assign_get_submissions.assignment.submission.plugin.editorfield
MoodleSubmissionFile = mod_assign_get_submissions.assignment.submission.plugin.filearea.file

MoodleGradeList = AssignmentGradeResponse.AssignmentList.Assignment.GradesList
MoodleGrade = MoodleGradeList.Grade
MoodleFileMeta = FileMetaDataResponse.FileList.File
