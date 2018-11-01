from . import pm, Argument

@pm.command(
    'upload files to draft area',
    Argument('files', nargs='+', help='files to upload', type=argparse.FileType('rb'))
)
def upload(files):
    frontend = MoodleFrontend(True)  # TODO: HACK, for not initializing worktree
    frontend.upload_files(files)


