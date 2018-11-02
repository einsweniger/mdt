#!/usr/bin/env python3

import sys

from frontend import commands
from persistence.worktree import NotInWorkTree

from persistence.config import get_global_config
from util import interaction


def check_for_sub_command():
    if 1 >= len(sys.argv):
        return None
    else:
        return sys.argv[1]


def check_config():
    cfg = get_global_config()
    missing = list(cfg.missing_values())
    while 0 != len(missing):
        if 'user_name' in missing:
            cfg.config.user_name = interaction.input_user_name()
        if 'token' in missing or 'user_id' in missing:
            cfg = commands.auth(url=cfg.config.url, user_name=cfg.config.user_name, service=cfg.config.service, cfg=cfg)
        missing = list(cfg.missing_values())
    return cfg


def main():
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
        main()
        print('exiting…')
    except KeyboardInterrupt:
        print('exiting…')
        raise SystemExit(1)
    except SystemExit:
        raise
    except NotInWorkTree as e:
        print(e)
        raise SystemExit(1)
    except Exception as e:
        print('onoz…')
        print(e)
        raise
