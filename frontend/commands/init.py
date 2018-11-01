from . import pm, Argument

@pm.command(
    'initialize work tree',
    Argument('-c', '--courseids', dest='course_ids', nargs='+', help='moodle course id', action='append')
)
def init(course_ids=None):
    """initializes working tree: creates local .mdt/config, with chosen courses"""

    wt = WorkTree(init=True)

    # ms = MoodleSession(moodle_url=url, token=token)
    frontend = MoodleFrontend(wt)

    # wrapped = wrappers.CourseListResponse(ms.get_users_course_list(user_id))
    wrapped = frontend.get_course_list()
    courses = list(wrapped)

    courses.sort(key=lambda course: course.full_name)

    saved_data = []
    if course_ids is None or force:
        choices = interaction.input_choices_from_list(courses, '\n  choose courses, seperate with space: ')
        if len(choices) == 0:
            print('nothing chosen.')
            raise SystemExit(0)
        chosen_courses = [courses[c] for c in choices]
        print('using:\n' + ' '.join([str(c) for c in chosen_courses]))
        course_ids = [c.id for c in chosen_courses]
        saved_data = [c for c in wrapped.raw if c['id'] in course_ids]

    wt.write_course_data(saved_data)

    wt.write_local_config({'courseids': str(course_ids)})

