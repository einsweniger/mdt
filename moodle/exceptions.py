from abc import abstractmethod


class _ExceptionRegistry(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = {}
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins[attrs['code']] = cls


class MoodleException(Exception, metaclass=_ExceptionRegistry):

    @property
    @abstractmethod
    def code(self):
        pass

    def __init__(self, exception, errorcode, message, debuginfo=''):
        self.exception_name = exception
        self.message = message
        self.error_code = errorcode
        self.debug_message = debuginfo

    def __str__(self):
        msg = 'Please Report this Exception!' \
              '\n {} <<{}>>' \
              '\n Message: {}' \
              '\n Debug:{}'.format(self.exception_name, self.error_code, self.message, self.debug_message)
        return msg

    @classmethod
    def generate_exception(cls, exception, errorcode, message, debuginfo = ''):
        try:
            return cls.plugins[errorcode](exception, errorcode, message, debuginfo)
        except KeyError:
            return cls(exception, errorcode, message, debuginfo)

    @classmethod
    def generate_error(cls, error, errorcode, stacktrace='', debuginfo = '', reproductionlink=''):
        try:
            return cls.plugins[errorcode](error, errorcode, stacktrace, debuginfo)
        except KeyError:
            return cls(error, errorcode, stacktrace, debuginfo)


class InvalidToken(MoodleException):
    code = 'invalidtoken'

    def __str__(self):
        return 'your token is invalid, try "mdt auth"?\n {}'.format(self.message)


class AccessException(MoodleException):
    code = 'accessexception'

    def __str__(self):
        return 'seems like you are not allowed to do this:\n {}'.format(self.message)


class AccessDenied(MoodleException):
    code = 'nopermissions'

    def __str__(self):
        return self.message


class InvalidResponse(MoodleException):
    code = 'invalidresponse'

    def __str__(self):
        return self.message + self.debug_message


class InvalidRecord(MoodleException):
    code = 'invalidrecord'

    def __str__(self):
        return self.message + self.debug_message

class InvalidLogin(MoodleException):
    code = 'invalidlogin'

    def __str__(self):
        return f'{self.error_code}: {self.exception_name}'

# webservice_access_exception accessexception Access Control Exception Invalid token - token expired - check validuntil time for the token

# when asking for a unknown module ID, translates to nothing found, I guess.
# {
#   "message": "Datensatz kann nicht in der Datenbank gefunden werden",
#   "exception": "dml_missing_record_exception",
#   "errorcode": "invalidrecordunknown"
#   "debuginfo": "SELECT md.name\n                                                 FROM {modules} md\n                                                 JOIN {course_modules} cm ON cm.module = md.id\n                                                WHERE cm.id = :cmid\n[array (\n  'cmid' => 117242,\n)]",
# }

generate_exception = MoodleException.generate_exception
generate_error = MoodleException.generate_error