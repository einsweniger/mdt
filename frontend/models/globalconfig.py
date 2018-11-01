from moodle.models import JsonDictWrapper


class GlobalConfig(JsonDictWrapper):
    @property
    def service(self) -> str:
        return self['service']

    @property
    def token(self) -> str:
        try:
            return self['token']
        except KeyError:
            token_not_found_msg = """
            'url' couldn't be found in your config file.
            Maybe it's corrupted.
            Either check the url in your config file
            or delete the entire file and create a new one.
            """
            raise SystemExit(token_not_found_msg)

    @property
    def user_id(self) -> int:
        try:
            return self['user_id']
        except KeyError:
            user_id_not_found_msg = """
            'user_id' couldn't be found in your config file.
            Maybe it's corrupted.
            Either check the url in your config file
            or delete the entire file and create a new one.
            """
            raise SystemExit(user_id_not_found_msg)

    @property
    def url(self) -> str:
        try:
            return self['url']
        except KeyError:
            url_not_found_msg = """
            'url' couldn't be found in your config file.
            Maybe it's corrupted.
            Either check the url in your config file
            or delete the entire file and create a new one.
            """
            raise SystemExit(url_not_found_msg)

    @property
    def user_name(self) -> str:
        return self['user_name']

    def add_overrides(self, overrides):
        if overrides is not None:
            self._data.update(overrides)

    def __str__(self):
        return str(self._data)

