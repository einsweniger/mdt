import argparse

from mdt import Context
from util import interaction
from . import pm, Argument
from concurrent import futures as cf
import json

@pm.command(
    'upload grades from files',
    Argument('grading_files', nargs='+', help='files containing grades', type=argparse.FileType())
)
def grade(grading_files):
    grades = []
    for file in grading_files:
        # cls needs to be set, for the strict flag to be registered.
        content = json.load(file, cls=json.JSONDecoder, strict=False)
        for grade in content['grades']:
            grades.append({
                'assignment_id': content['assignment'],
                'user_id': grade['uid'],
                'grade': grade['grade'],
                'feedback_text': grade['feedback'],
                'team_submission': content['team']
            })
    grade_count = len(grades)
    counter = 0
    if grade_count == 0:
        return
    interaction.print_progress(counter, grade_count)
    session = Context.get_session()
    with cf.ThreadPoolExecutor(max_workers=Context.MAX_WORKERS) as tpe:
        try:
            future_to_grade = {tpe.submit(session.mod_assign_save_grade, **args): args for args in grades}
            for future in cf.as_completed(future_to_grade):
                args = future_to_grade[future]
                response = future.result()
                counter += 1
                interaction.print_progress(counter, grade_count)
        except KeyboardInterrupt:
            print('stopping…')
            tpe.shutdown()
            raise
    #upload_data = parse_grade_files(grading_files)

    #upload_grades(upload_data)


def parse_grade_files(fd_list):
    """
    this mostly rewrites the values read from the grading file.
    since most of this can be done, when creating the grading file
    it should be done there.
    Namely, adding a team_submission field and instead of
    setting the submission.id in the file, use the user.id instead

    :param fd_list:
    :return:
    """

    upload_data = []

    print('this will upload the following grades:')
    grade_format = '  {:>20}:{:6d} {:5.1f} > {}'

    invalid_values = []
    wt = Context.get_work_tree()

    for file in fd_list:
        # cls needs to be set, for the strict flag to be registered.
        wrapped = GradingFile(json.load(file, cls=json.JSONDecoder, strict=False))

        assignment = MoodleAssignment(wt.meta.assignments[wrapped.assignment_id])
        assignment.course = Course(wt.meta.courses[assignment.courseid])

        assignment.course.parse_users(wt.meta.users[str(assignment.course_id)])
        assignment.parse_submissions(wt.meta.submissions[assignment.id])

        wrapped.team_submission = assignment.is_team_submission

        print(f' assignment {assignment.id:5d}, team_submission: {assignment.is_team_submission}')

        for grade in wrapped.grades:
            submission = assignment.submissions[grade.id]

            if assignment.is_team_submission:
                group = assignment.course.groups[submission.group_id]
                user = group.members[0]
                grade.id = user.id
            else:
                grade.id = submission.user_id

            if assignment.max_points < grade.grade:
                invalid_values.append(grade)

            print(grade_format.format(grade.name, grade.id, grade.grade, grade.feedback[:40]))

        upload_data.append(wrapped)

    if len(invalid_values) > 0:
        for grade in invalid_values:
            print(
                "WARNING: the grade value is larger than the max achievable grade")
            print(grade_format.format(grade.name, grade.id, grade.grade, grade.feedback[:40]))
        raise SystemExit(1)

    answer = input('does this look good? [Y/n]: ')

    if 'n' == answer:
        print('do it right, then')
        raise SystemExit(0)
    elif not ('y' == answer.lower() or '' == answer):
        print('wat')
        raise SystemExit(1)

    return upload_data


def upload_grades(upload_data):
    def argument_list(upload_data):
        for grades in upload_data:
            as_id = grades.assignment_id
            team = grades.team_submission
            args = []
            for values in grades.grades:
                args.append({
                    'assignment_id': as_id,
                    'user_id': values.id,
                    'grade': values.grade,
                    'feedback_text': values.feedback,
                    'team_submission': team
                })
            return args

    args_list = argument_list(upload_data)
    grade_count = len(args_list)
    counter = 0

    if grade_count == 0:
        return
    interaction.print_progress(counter, grade_count)
    session = Context.get_session()
    with cf.ThreadPoolExecutor(max_workers=Context.MAX_WORKERS) as tpe:
        try:
            future_to_grade = {tpe.submit(session.mod_assign_save_grade, **args): args for args in args_list}
            for future in cf.as_completed(future_to_grade):
                args = future_to_grade[future]
                response = future.result()
                counter += 1
                interaction.print_progress(counter, grade_count)
        except KeyboardInterrupt:
            print('stopping…')
            tpe.shutdown()
            raise
