from . import pm, Argument

@pm.command(
    'retrieve files for grading',
    Argument('assignment_ids', nargs='*', type=int),
    Argument('--all', help='pull all due submissions, even old ones', action='store_true')
)
def pull(assignment_ids=None, all=False):
    frontend = MoodleFrontend()

    frontend.download_files(assignment_ids)


