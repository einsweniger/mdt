from . import pm

@pm.command(
    'dump course contents, work in progress'
)
def dump():
    frontend = MoodleFrontend()

    frontend.get_course_content()


