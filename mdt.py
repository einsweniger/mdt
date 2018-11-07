#!/usr/bin/env python3

import sys
import asyncio
from frontend import commands
from moodle.exceptions import MoodleException

from persistence.worktree import NotInWorkTree

from util import interaction

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from persistence.worktree import WorkTree
    from moodle.communication import MoodleSession
    from persistence.config import get_global_config, GlobalConfig


class Context:
    WT: 'WorkTree' = None
    MS: 'MoodleSession' = None
    CFG: 'GlobalConfig' = None
    MAX_WORKERS: int = 10

    @classmethod
    def get_work_tree(cls) -> 'WorkTree':
        if cls.WT is None:
            from persistence.worktree import WorkTree
            cls.WT = WorkTree()
        return cls.WT

    @classmethod
    def get_config(cls) -> 'GlobalConfig':
        if cls.CFG is None:
            from persistence.config import get_global_config
            cls.CFG = get_global_config()
        return cls.CFG

    @classmethod
    def get_session(cls) -> 'MoodleSession':
        if cls.MS is None:
            from moodle.communication import MoodleSession
            cls.MS = MoodleSession(cls.get_config().config.url)
        return cls.MS


def check_for_sub_command():
    if 1 >= len(sys.argv):
        return None
    else:
        return sys.argv[1]


def check_config():
    cfg = Context.get_config()
    missing = list(cfg.missing_values())
    while 0 != len(missing):
        if 'user_name' in missing:
            cfg.config.user_name = interaction.input_user_name()
        if 'token' in missing or 'user_id' in missing:
            cfg = commands.auth(url=cfg.config.url, user_name=cfg.config.user_name, service=cfg.config.service, cfg=cfg)
        missing = list(cfg.missing_values())
    return cfg


async def main():
    check_config()
    sub_command = check_for_sub_command()

    if sub_command is None:
        commands.make_config_parser().print_help()
        raise SystemExit(1)
    elif sub_command in commands.pm.known_commands:
        parser = commands.make_config_parser()
        args, unknown = parser.parse_known_args()
        if 'func' in args:
            kwargs = vars(args)
            func = kwargs.pop('func')
            func(**kwargs)
        else:
            call = getattr(commands, sub_command)
            call()
    else:
        commands.make_config_parser().print_help()
        raise SystemExit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
        print('exiting…')
    except KeyboardInterrupt:
        print('exiting…')
        raise SystemExit(1)
    except SystemExit:
        raise
    except NotInWorkTree as e:
        print(e)
        raise SystemExit(1)
    except MoodleException as e:
        print(f'error: moodle had a problem:\n {e}')
    except Exception as e:
        print('onoz…')
        print(e)
        raise
