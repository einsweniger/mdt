from util import interaction
from . import pm, Argument
from mdt import Context
import json

@pm.command(
    'enrol in a course',
    Argument('keywords', nargs='+', help='some words to search for')
)
def enrol(keywords):

    data = search_courses_by_keywords(keywords)
    courses = [c for c in data['courses']]
    courses.sort(key=lambda d: d['fullname'])

    print('received {} courses'.format(data['total']))
    course_strs = []
    for course in courses:
        course_strs.append(
            '{:40} {:5d} {:20} {}'.format(course['fullname'][:39], course['id'], course['shortname'][:19],
                                          str(set(course['enrollmentmethods'])))
        )

    choices = interaction.input_choices_from_list(course_strs, '\n  choose one course: ')
    if len(choices) == 0:
        print('nothing chosen.')
        raise SystemExit(1)
    elif len(choices) > 1:
        print('please choose only one, to enrol in')
        raise SystemExit(1)

    chosen_course = courses[choices[0]]
    # print('using:\n' + ' '.join([str(c[Jn.short_name]) for c in chosen_course]))
    # reply = ms.get_course_enrolment_methods(chosen_course[Jn.id])

    enrolment_methods = get_course_enrolment_methods(chosen_course['id'])
    chosen_method_instance_id = None
    if len(enrolment_methods) > 1:
        print(json.dumps(enrolment_methods, indent=2, sort_keys=True))
        # todo: let user choose enrolment method
        raise NotImplementedError('there are multiple enrolment methods, please send this output as bugreport')
    elif len(enrolment_methods) == 1:
        if enrolment_methods[0]['status']:
            chosen_method_instance_id = enrolment_methods[0]['id']

    if chosen_method_instance_id is None:
        # no active enrolment method
        print('No available enrolment method, sorry')
        raise SystemExit(0)
    # todo: if wsfunction in enrolment method, try that. on accessexception, try without password.
    # todo: if without password fails, possibly warning code 4, then ask for password

    answer = enrol_in_course(chosen_course[Jn.id], instance_id=chosen_method_instance_id)
    if not answer['status'] and 'warnings' in answer:
        warning = answer['warnings'][0]
        if warning['warningcode'] == '4':  # wrong password?
            unsuccessful = True
            while unsuccessful:
                print(warning['message'])
                # todo, move to utils.interaction
                password = getpass.getpass(prompt='enrolment key: ')
                data = enrol_in_course(chosen_course['id'], password=password,
                                                instance_id=chosen_method_instance_id)

                if data['status']:
                    unsuccessful = False
                    # todo: this is pretty hacky and error prone, fix possibly soon, or maybe not. this has no priority.



def search_courses_by_keywords(keyword_list):
    # TODO: wrap and return to wstools.enrol
    response = Context.get_session().core_course_search_courses(' '.join(keyword_list))
    return response

def get_course_enrolment_methods(course_id):
    # TODO: wrap and return to wstools.enrol
    response = Context.get_session().core_enrol_get_course_enrolment_methods(course_id)
    return response

def enrol_in_course(course_id, instance_id, password=''):
    # TODO: wrap and return to wstools.enrol
    response = Context.get_session().enrol_self_enrol_user(course_id, instance_id=instance_id, password=password)
    return response
