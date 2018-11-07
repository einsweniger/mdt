# interesting things:
# inspect.signature for plugins
# multithreading https://docs.python.org/3/tutorial/stdlib2.html#multi-threading
# also: multiprocessing http://python-3-patterns-idioms-test.readthedocs.io/en/latest/CoroutinesAndConcurrency.html
# unittests https://docs.python.org/3/library/unittest.html
import logging

from frontend.cmdparser import ParserManager, Argument, ArgumentGroup

log = logging.getLogger('wstools')
pm = ParserManager('wstools', 'internal sub command help')

from .auth import auth
# from .config import config
from .dump import dump
from .enrol import enrol
from .fetch import fetch
from .grade import grade
from .init import init
from .pull import pull
from .status import status
from .submit import submit
# from .upload import upload
from .clone import clone


def make_config_parser():
    return pm.parser


