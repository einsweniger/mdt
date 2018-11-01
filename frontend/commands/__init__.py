# interesting things:
# inspect.signature for plugins
# multithreading https://docs.python.org/3/tutorial/stdlib2.html#multi-threading
# also: multiprocessing http://python-3-patterns-idioms-test.readthedocs.io/en/latest/CoroutinesAndConcurrency.html
# unittests https://docs.python.org/3/library/unittest.html
import argparse
import getpass
import json
import logging
import shutil

from frontend import MoodleFrontend
from frontend.models import Course, Assignment
from moodle.fieldnames import JsonFieldNames as Jn, text_format
from persistence.worktree import WorkTree
from util import interaction
from frontend.cmdparser import ParserManager, Argument, ArgumentGroup

log = logging.getLogger('wstools')
pm = ParserManager('wstools', 'internal sub command help')

from .auth import auth


def make_config_parser():
    return pm.parser


