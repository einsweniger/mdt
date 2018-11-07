import inspect
from abc import abstractmethod
from collections import Mapping, Sequence, Sized, namedtuple as nt
from dataclasses import dataclass, is_dataclass
import dataclasses as dc
from typing import List, Any, Union, Sequence, Optional
import collections
from datetime import datetime
import typing
import logging
import json

DEBUG = True
log = logging.getLogger('moodle.responses')
T = typing.TypeVar('T')


def destructuring_list_cast(cls: typing.Callable[[dict], T]) -> typing.Callable[[list], T]:
    def cast(data: list) -> List[T]:
        if data is None:
            return []

        if not isinstance(data, list):
            raise SystemExit(f'listcast expects a list, you sent: {type(data)}')
        try:
            return [cls(**entry) for entry in data]
        except TypeError as err:
            print(inspect.signature(cls))
            provided = set()
            for x in data:
                provided.update(set(x.keys()))
            expected = set(inspect.signature(cls).parameters.keys())
            if len(expected) == 0:
                raise SystemExit(f'implementing class {cls} has empty signature. did you forget to add @dataclass?')
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
            for ep in sorted(provided.difference(expected)):
                print(f'    {ep}')

            raise SystemExit(f'listcast for class {cls} failed:\n{err}')

    return cast


# destructured_cast_field
def dcf(cls):
    return dc.field(metadata={'castfunc': destructuring_list_cast(cls)})


def optional_dcf(cls):
    return dc.field(metadata={'castfunc': destructuring_list_cast(cls)}, default_factory=list)


def is_generic(cls):
    # return cls is typing._GenericAlias
    def check(cls):
        try:
            return '__origin__' in cls.__dict__
        except AttributeError:
            return False
    # print(f'is_generic: {check(cls)} {cls}')
    return check(cls)




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
            if is_generic(expected):
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

    def _typecheck_generic(self, expected, actual, depth=0):
        assert '__origin__' in expected.__dict__
        # print(f'typecheck, depth {depth}')
        if expected.__origin__ is typing.Union:
            for arg in expected.__args__:
                # print(f'at depth: {depth}, is_generic: {is_generic(arg)}, expected_arg {arg}')
                if is_generic(arg):
                    return self._typecheck_generic(arg, actual, depth+1)
                if actual is arg:
                    return True
            else:
                print(f'specified Union {expected} does not contain {actual}')
                return False
        if expected.__origin__ is list:
            # print(f'idunno, List expected: {expected} is {actual}')
            # print(dir(actual))
            return True
        raise RuntimeError('this was an unexpected generic')


@dataclass
class DCcore_enrol_get_users_courses(BaseDC):
    id: int  # id of course
    shortname: str  # short name of course
    fullname: str  # long name of course
    enrolledusercount: int  # Number of enrolled users in this course
    idnumber: str  # id number of course
    visible: int  # 1 means visible, 0 means hidden course
    summary: Optional[str] = None  # summary
    summaryformat: Optional[int] = None  # summary format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
    format: Optional[str] = None  # course format: weeks, topics, social, site
    showgrades: Optional[int] = None  # true if grades are shown, otherwise false
    lang: Optional[str] = None  # forced course language
    enablecompletion: Optional[int] = None  # true if completion is enabled, otherwise false
    category: Optional[int] = None  # course category id
    progress: Optional[float] = None  # Progress percentage
    startdate: Optional[int] = None  # Timestamp when the course start
    enddate: Optional[int] = None  # Timestamp when the course end

    def __str__(self): return f'{self.fullname[0:39]:40} id:{self.id:5d} short: {self.shortname}'


core_enrol_get_users_courses = destructuring_list_cast(DCcore_enrol_get_users_courses)


@dataclass
class DCcore_enrol_get_enrolled_users(BaseDC):
    @dataclass
    class customfield(BaseDC):
        type: str  # The type of the custom field - text field, checkbox...
        value: str  # The value of the custom field
        name: str  # The name of the custom field
        shortname: str  # The shortname of the custom field - to be able to build the field class in the code

    @dataclass
    class group(BaseDC):
        id: int  # group id
        name: str  # group name
        description: str  # group description
        descriptionformat: int  # description format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)

    @dataclass
    class role(BaseDC):
        roleid: int  # role id
        name: str  # role name
        shortname: str  # role shortname
        sortorder: int  # role sortorder

    @dataclass
    class preference(BaseDC):
        name: str  # The name of the preferences
        value: str  # The value of the custom field

    @dataclass
    class enrolledcourse(BaseDC):
        id: int  # Id of the course
        fullname: str  # Fullname of the course
        shortname: str  # Shortname of the course

    id: int  # ID of the user
    fullname: str  # The fullname of the user

    customfields: Optional[List[customfield]] = optional_dcf(
        customfield)  # User custom fields (also known as user profil fields)
    groups: Optional[List[group]] = optional_dcf(group)  # user groups
    roles: Optional[List[role]] = optional_dcf(role)  # user roles
    preferences: Optional[List[preference]] = optional_dcf(preference)  # User preferences
    enrolledcourses: Optional[List[enrolledcourse]] = optional_dcf(
        enrolledcourse)  # Courses where the user is enrolled - limited by which courses the user is able to see

    username: Optional[str] = None  # Username policy is defined in Moodle security config
    firstname: Optional[str] = None  # The first name(s) of the user
    lastname: Optional[str] = None  # The family name of the user
    email: Optional[str] = None  # An email address - allow email as root@localhost
    address: Optional[str] = None  # Postal address
    phone1: Optional[str] = None  # Phone 1
    phone2: Optional[str] = None  # Phone 2
    icq: Optional[str] = None  # icq number
    skype: Optional[str] = None  # skype id
    yahoo: Optional[str] = None  # yahoo id
    aim: Optional[str] = None  # aim id
    msn: Optional[str] = None  # msn number
    department: Optional[str] = None  # department
    institution: Optional[str] = None  # institution
    idnumber: Optional[str] = None  # An arbitrary ID code number perhaps from the institution
    interests: Optional[str] = None  # user interests (separated by commas)
    firstaccess: Optional[int] = None  # first access to the site (0 if never)
    lastaccess: Optional[int] = None  # last access to the site (0 if never)
    description: Optional[str] = None  # User profile description
    descriptionformat: Optional[int] = None  # description format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
    city: Optional[str] = None  # Home city of the user
    url: Optional[str] = None  # URL of the user
    country: Optional[str] = None  # Home country code of the user, such as AU or CZ
    profileimageurlsmall: Optional[str] = None  # User image profile URL - small version
    profileimageurl: Optional[str] = None  # User image profile URL - big version


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
            name: str  # assignment name
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
            attemptreopenmethod: str  # method used to control opening new attempts
            maxattempts: int  # maximum number of attempts allowed
            markingworkflow: int  # enable marking workflow
            markingallocation: int  # enable marking allocation
            requiresubmissionstatement: int  # student must accept submission statement

            @dataclass
            class config(BaseDC):  # assignment configuration object
                plugin: str  # plugin
                subtype: str  # subtype
                name: str  # name
                value: str  # value
                id: Optional[int] = None  # assign_plugin_config id
                assignment: Optional[int] = None  # assignment id

                def __str__(self):
                    return f'{self.plugin}:{self.subtype}:{self.name}:{self.value}'

            @dataclass
            class introfile(BaseDC):  # File.
                filename: Optional[str] = None  # File name.
                filepath: Optional[str] = None  # File path.
                filesize: Optional[int] = None  # File size.
                fileurl: Optional[str] = None  # Downloadable file url.
                timemodified: Optional[int] = None  # Time modified.
                mimetype: Optional[str] = None  # File mime type.
                isexternalfile: Optional[int] = None  # Whether is an external file.
                repositorytype: Optional[str] = None  # The repository type for external files.

            @dataclass
            class introattachment(BaseDC):  # File.
                filename: Optional[str] = None  # File name.
                filepath: Optional[str] = None  # File path.
                filesize: Optional[int] = None  # File size.
                fileurl: Optional[str] = None  # Downloadable file url.
                timemodified: Optional[int] = None  # Time modified.
                mimetype: Optional[str] = None  # File mime type.
                isexternalfile: Optional[int] = None  # Whether is an external file.
                repositorytype: Optional[str] = None  # The repository type for external files.

            configs: List[config] = dcf(config)  # configuration settings
            introfiles: Optional[List[introfile]] = optional_dcf(introfile)  # Files in the introduction text
            introattachments: Optional[List[introattachment]] = optional_dcf(introattachment)  # intro attachments files

            preventsubmissionnotingroup: Optional[int] = None  # Prevent submission not in group

            # Submission statement formatted.
            submissionstatement: Optional[str] = None
            # submissionstatement format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
            submissionstatementformat: Optional[int] = None

            # assignment intro, not allways returned because it deppends on the activity configuration
            intro: Optional[str] = None
            # intro format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
            introformat: Optional[int] = None

        id: int  # course id
        fullname: str  # course full name
        shortname: str  # course short name
        timemodified: int  # last time modified
        assignments: List[assignment] = dcf(
            assignment)  # assignment info # list of ( object {  # assignment information object

    @dataclass
    class warning(BaseDC):
        warningcode: str  # errorcode can be 1 (no access rights) or 2 (not enrolled or no permissions)
        message: str  # untranslated english message to explain the warning

        # When item is a course then itemid is a course id. When the item is a module then itemid is a module id
        itemid: Optional[int] = None
        item: Optional[str] = None  # item can be 'course' (errorcode 1 or 2) or 'module' (errorcode 1)

    courses: List[course] = dcf(course)  # list of courses
    warnings: Optional[List[warning]] = optional_dcf(warning)  # list of warnings


@dataclass
class mod_assign_get_submissions(BaseDC):
    @dataclass
    class warning(BaseDC):
        warningcode: str  # the warning code can be used by the client app to implement specific behaviour
        message: str  # untranslated english message to explain the warning
        item: Optional[str] = None  # item
        itemid: Optional[int] = None  # item id

    @dataclass
    class assignment(BaseDC):
        @dataclass
        class submission(BaseDC):
            id: int  # submission id
            userid: int  # student id
            attemptnumber: int  # attempt number
            timecreated: int  # submission creation time
            timemodified: int  # submission last modified time
            status: str  # submission status
            groupid: int  # group id

            @dataclass
            class plugin(BaseDC):
                type: str  # submission plugin type
                name: str  # submission plugin name

                @dataclass
                class editorfield(BaseDC):
                    name: str  # field name
                    description: str  # field description
                    text: str  # field value
                    format: int  # text format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)

                @dataclass
                class filearea(BaseDC):
                    area: str  # file area
                    @dataclass
                    class file(BaseDC):
                        filename: Optional[str] = None  # File name.
                        filepath: Optional[str] = None  # File path.
                        filesize: Optional[int] = None  # File size.
                        fileurl: Optional[str] = None  # Downloadable file url.
                        timemodified: Optional[int] = None  # Time modified.
                        mimetype: Optional[str] = None  # File mime type.
                        isexternalfile: Optional[int] = None  # Whether is an external file.
                        repositorytype: Optional[str] = None  # The repository type for external files.
                    files: Optional[List[file]] = optional_dcf(file)  # files


                editorfields: Optional[List[editorfield]] = optional_dcf(editorfield)  # editorfields
                fileareas: Optional[List[filearea]] = optional_dcf(filearea)  # fileareas

            plugins: Optional[List[plugin]] = optional_dcf(plugin)  # plugins
            assignment: Optional[int] = None  # assignment id
            latest: Optional[int] = None  # latest attempt

            gradingstatus: Optional[str] = None  # Grading status.

        assignmentid: int  # assignment id
        submissions: List[submission] = dcf(submission)  # submission info

    assignments: List[assignment] = dcf(assignment)  # assignment submissions
    warnings: Optional[List[warning]] = optional_dcf(warning)  # list of warnings


@dataclass
class core_files_get_files(BaseDC):
    @dataclass
    class parent(BaseDC):
        contextid: int
        component: str
        filearea: str
        itemid: int
        filepath: str
        filename: str

    @dataclass
    class file(BaseDC):
        contextid: int
        component: str
        filearea: str
        itemid: int
        filepath: str
        filename: str
        isdir: int
        url: str
        timemodified: int
        timecreated: Optional[int] = None  # Time created
        filesize: Optional[int] = None  # File size
        author: Optional[str] = None  # File owner
        license: Optional[str] = None  # File license

    parents: List[parent] = dcf(parent)
    files: List[file] = dcf(file)

@dataclass
class DCcore_course_get_contents(BaseDC):
    @dataclass
    class module(BaseDC):
        id: int  # activity id
        modicon: str  # activity icon url
        modname: str  # activity module type
        modplural: str  # activity module plural name
        indent: int  # number of identation in the site
        name: str  # activity module name

        @dataclass
        class content(BaseDC):
            type: str  # a file or a folder or external link
            filename: str  # filename
            filepath: str  # filepath
            filesize: int  # filesize
            timecreated: int  # Time created
            timemodified: int  # Time modified
            sortorder: int  # Content sort order
            userid: int  # User who added this content to moodle
            author: str  # Content owner
            license: str  # Content license
            fileurl: Optional[str] = None  # downloadable file url
            content: Optional[str] = None  # Raw content, will be used when type is content
            mimetype: Optional[str] = None  # File mime type.
            isexternalfile: Optional[int] = None  # Whether is an external file.
            repositorytype: Optional[str] = None  # The repository type for external files.

        contents: List[content] = optional_dcf(content)
        url: Optional[str] = None  # activity url
        instance: Optional[int] = None  # instance id
        description: Optional[str] = None  # activity description
        visible: Optional[int] = None  # is the module visible
        uservisible: Optional[int] = None  # Is the module visible for the user?
        availabilityinfo: Optional[str] = None  # Availability information.
        visibleoncoursepage: Optional[int] = None  # is the module visible on course page
        availability: Optional[str] = None  # module availability settings

    id: int  # Section ID
    name: str  # Section name
    summary: str  # Section description
    summaryformat: int  # summary format (1 = HTML, 0 = MOODLE, 2 = PLAIN or 4 = MARKDOWN)
    modules: List[module] = dcf(module)  # list of module
    section: Optional[int] = None  # Section number inside the course
    hiddenbynumsections: Optional[int] = None  # Whether is a section hidden in the course format
    uservisible: Optional[int] = None  # Is the section visible for the user?
    availabilityinfo: Optional[str] = None  # Availability information.
    visible: Optional[int] = None  # is the section visible


core_course_get_contents = destructuring_list_cast(DCcore_course_get_contents)


@dataclass
class mod_assign_get_grades(BaseDC):
    @dataclass
    class assignment(BaseDC):
        assignmentid: int  # assignment id

        @dataclass
        class grade(BaseDC):
            id: int  # grade id
            userid: int  # student id
            attemptnumber: int  # attempt number
            timecreated: int  # grade creation time
            timemodified: int  # grade last modified time
            grader: int  # grader
            grade: str  # grade
            assignment: Optional[int] = None  # assignment id
            gradefordisplay: Optional[str] = None  # grade rendered into a format suitable for display

        grades: List[grade] = dcf(grade)

    assignments: List[assignment] = dcf(assignment)  # list of assignment grade information

    @dataclass
    class warning(BaseDC):
        warningcode: str  # errorcode can be 3 (no grades found) or 1 (no permission to get grades)
        message: str  # untranslated english message to explain the warning
        item: Optional[str] = None  # item is always 'assignment'
        itemid: Optional[
            int] = None  # when errorcode is 3 then itemid is an assignment id. When errorcode is 1, itemid is a course module id

    warnings: Optional[List[warning]] = optional_dcf(warning)  # list of warnings


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


# used in session.upload_files
# https://github.com/moodle/moodle/blob/MOODLE_35_STABLE/webservice/upload.php
@dataclass
class DCmoodle_upload(BaseDC):
    @dataclass
    class file_record(BaseDC):
        # fields that are present on both error and success:
        filename: str  # $file->filename;

        # only on success
        filepath: Optional[str] = None  # $filepath;
        component: Optional[str] = None  # 'user';
        contextid: Optional[int] = None  # $context->id;
        userid: Optional[int] = None  # $USER->id;
        filearea: Optional[str] = None  # 'draft';
        itemid: Optional[int] = None  # $itemid;
        license: Optional[str] = None  # $CFG->sitedefaultlicense;
        author: Optional[str] = None  # fullname($authenticationinfo['user']);
        source: Optional[str] = None  # serialize((object)array('source' => $file->filename));


        # only with error
        errortype: Optional[str] = None
        error: Optional[str] = None

    file_records: List[file_record] = dcf(file_record)


moodle_upload = destructuring_list_cast(DCmoodle_upload)


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

MoodleFileMeta = core_files_get_files.file

MoodleGradeList = destructuring_list_cast(mod_assign_get_grades.assignment.grade)
MoodleGrade = mod_assign_get_grades.assignment.grade
