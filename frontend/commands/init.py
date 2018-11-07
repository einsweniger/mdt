from mdt import Context
from util import interaction
from . import pm, Argument
from persistence.worktree import WorkTree
from moodle import responses
from dataclasses import asdict


@pm.command(
    'initialize work tree',
    Argument('-c', '--courseids', dest='course_ids', nargs='+', help='moodle course id', action='append')
)
def init(course_ids=None):
    """initializes working tree: creates local .mdt/config, with chosen courses"""

    wt = WorkTree(init=True)
    session = Context.get_session()
    uid = Context.get_config().config.user_id

    # ms = MoodleSession(moodle_url=url, token=token)

    # wrapped = wrappers.CourseListResponse(ms.get_users_course_list(user_id))

    raw = session.core_enrol_get_users_courses(uid)
    courses = responses.core_enrol_get_users_courses(raw)
    # courses = list(response)

    courses.sort(key=lambda x: x.fullname)

    saved_data = []
    if course_ids is None:
        choices = interaction.input_choices_from_list(courses, '\n  choose courses, seperate with space: ')
        if len(choices) == 0:
            print('nothing chosen.')
            raise SystemExit(0)
        chosen_courses = [courses[c] for c in choices]
        print('using:\n' + '\n'.join([str(c) for c in chosen_courses]))
        course_ids = [c.id for c in chosen_courses]
    saved_data = [c for c in raw if c['id'] in course_ids]

    wt.meta.write_course_data(saved_data)

    #wt.meta.write_course_data({'courseids': str(course_ids)})
