from . import pm, Argument

@pm.command(
    'enrol in a course',
    Argument('keywords', nargs='+', help='some words to search for')
)
def enrol(keywords):
    frontend = MoodleFrontend(True)
    data = frontend.search_courses_by_keywords(keywords)
    courses = [c for c in data['courses']]
    courses.sort(key=lambda d: d['fullname'])

    print('received {} courses'.format(data['total']))
    course_strs = []
    for course in courses:
        course_strs.append(
            '{:40} {:5d} {:20} {}'.format(course[Jn.full_name][:39], course[Jn.id], course[Jn.short_name][:19],
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

    enrolment_methods = frontend.get_course_enrolment_methods(chosen_course[Jn.id])
    chosen_method_instance_id = None
    if len(enrolment_methods) > 1:
        print(json.dumps(enrolment_methods, indent=2, sort_keys=True))
        # todo: let user choose enrolment method
        raise NotImplementedError('there are multiple enrolment methods, please send this output as bugreport')
    elif len(enrolment_methods) == 1:
        if enrolment_methods[0][Jn.status]:
            chosen_method_instance_id = enrolment_methods[0][Jn.id]

    if chosen_method_instance_id is None:
        # no active enrolment method
        print('No available enrolment method, sorry')
        raise SystemExit(0)
    # todo: if wsfunction in enrolment method, try that. on accessexception, try without password.
    # todo: if without password fails, possibly warning code 4, then ask for password

    answer = frontend.enrol_in_course(chosen_course[Jn.id], instance_id=chosen_method_instance_id)
    if not answer[Jn.status] and Jn.warnings in answer:
        warning = answer[Jn.warnings][0]
        if warning[Jn.warning_code] == '4':  # wrong password?
            unsuccessful = True
            while unsuccessful:
                print(warning[Jn.message])
                # todo, move to utils.interaction
                password = getpass.getpass(prompt='enrolment key: ')
                data = frontend.enrol_in_course(chosen_course[Jn.id], password=password,
                                                instance_id=chosen_method_instance_id)

                if data[Jn.status]:
                    unsuccessful = False
                    # todo: this is pretty hacky and error prone, fix possibly soon, or maybe not. this has no priority.


