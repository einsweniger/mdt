from . import pm, Argument

@pm.command(
    'upload grades from files',
    Argument('grading_files', nargs='+', help='files containing grades', type=argparse.FileType())
)
def grade(grading_files):
    frontend = MoodleFrontend()
    upload_data = frontend.parse_grade_files(grading_files)

    frontend.upload_grades(upload_data)


