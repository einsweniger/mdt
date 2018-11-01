from . import pm, Argument

@pm.command(
    'download metadata from server',
    Argument('-a', '--assignments', help='sync assignments', action='store_true'),
    Argument('-s', '--submissions', help='sync submissions', action='store_true'),
    Argument('-g', '--grades', help='sync grades', action='store_true'),
    Argument('-u', '--users', help='sync users', action='store_true', default=False),
    Argument('-f', '--files', help='sync file metadata', action='store_true', default=False)
)
def sync(assignments=False, submissions=False, grades=False, users=False, files=False):
    frontend = MoodleFrontend()

    sync_all = True
    if users or submissions or assignments or grades or files:
        sync_all = False

    if assignments or sync_all:
        print('syncing assignments… ', end='', flush=True)
        output = frontend.sync_assignments()
        print('finished. ' + ' '.join(output))

    if submissions or sync_all:
        print('syncing submissions… ', end='', flush=True)
        output = frontend.sync_submissions()
        print('finished. ' + ' '.join(output))

    if grades or sync_all:
        print('syncing grades… ', end='', flush=True)
        output = frontend.sync_grades()
        print('finished. ' + ' '.join(output))

    if users or sync_all:
        print('syncing users…', end=' ', flush=True)
        output = frontend.sync_users()
        print(output + 'finished.')

    if files:  # TODO: when finished, add 'or sync_all'
        print('syncing files… ', end='', flush=True)
        frontend.sync_file_meta_data()
        print('finished')

