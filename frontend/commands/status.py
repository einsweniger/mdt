from . import pm, Argument

@pm.command(
    'display various information about work tree',
    Argument('-a', '--assignmentids', dest='assignment_ids', nargs='+',
             help='show detailed status for assignment id', type=int),
    Argument('-s', '--submissionids', dest='submission_ids', nargs='+',
             help='show detailed status for submission id', type=int),
    Argument('--full', help='display all assignments', action='store_true')
)
def status(assignment_ids=None, submission_ids=None, full=False):
    wt = WorkTree()
    term_columns = shutil.get_terminal_size().columns

    if assignment_ids is not None and submission_ids is None:
        for assignment_id in assignment_ids:
            assignment = Assignment(wt.assignments[assignment_id])
            assignment.course = Course(wt.courses[assignment.course_id])
            assignment.course.parse_users(wt.users[str(assignment.course_id)])
            assignment.parse_submissions(wt.submissions[assignment_id])
            try:
                assignment.parse_grades(wt.grades[assignment_id])
            except KeyError:
                assignment.parse_grades(None)

            print(assignment.course)
            print(assignment.detailed_status_string(indent=1))

    elif submission_ids is not None:
        courses = wt.data
        # TODO this.
        for course in sorted(courses, key=lambda c: c.name):
            print(course)
            assignments = course.sync_assignments(assignment_ids)
            a_status = [a.detailed_status_string() for a in assignments]
            for s in sorted(a_status):
                print(s)
    elif full:
        courses = wt.data
        for course in sorted(courses, key=lambda c: c.name):
            course.print_status()
    else:
        courses = wt.data
        for course in sorted(courses, key=lambda c: c.name):
            course.print_short_status()

