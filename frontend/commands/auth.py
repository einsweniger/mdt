from moodle.communication import MoodleSession
from moodle.exceptions import InvalidLogin
from persistence.config import GlobalConfig, get_global_config
from util import interaction
from . import pm, Argument

@pm.command(
    'retrieve access token from server',
    Argument('-u', '--user', dest='user_name', help='username', required=False),
    Argument('--host', dest='url', help='the moodle host name', required=False),
    Argument('-a', '--ask', help='will ask for all credentials, again', action='store_true'),
    Argument('-s', '--service', help='the webservice, has to be set explicitly, defaults to mobile api',
             default='moodle_mobile_app'),
)
def auth(url=None, ask=False, user_name=None, service='moodle_mobile_app', cfg: GlobalConfig=None) -> GlobalConfig:
    """
    Retreives a Web Service Token for the given user and host and saves it to the global config.

    :param cfg: a GlobalConfig to modify
    :param url: the moodle host
    :param ask: set this to true, to get asked for input of known values anyway.
    :param user_name: the login for which you'd like to retrieve a token for.
    :param service: the configured Web Service, you'd like the token for.
    :return: nothing.
    """
    if cfg is None:
        cfg = get_global_config()
    url = url or cfg.config.url
    user_name = user_name or cfg.config.user_name

    if ask:
        url = interaction.input_moodle_url(url)
        user_name = interaction.input_user_name(user_name)
    else:
        if url is None or url.strip() == '':
            url = interaction.input_moodle_url()

        if user_name is None or user_name.strip() == '':
            user_name = interaction.input_user_name()

    session = MoodleSession(moodle_url=url)

    while True:
        try:
            password = interaction.input_password()

            response = session.get_token(user_name, password, service)
            session.token = cfg.config.token = response.token
            del password
        except InvalidLogin as e:
            print(e)

        print(f'got token, requesting user info')
        # Writing values here once, to allow MoodleFrontend to read from it.
        data = session.core_webservice_get_site_info()

        cfg.config.user_id = data['userid']
        cfg.write()
        return cfg
