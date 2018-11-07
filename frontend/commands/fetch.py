from . import pm, Argument
from datetime import datetime
from mdt import Context
import math
from moodle import responses
from moodle.exceptions import AccessDenied, InvalidResponse
import re


@pm.command(
    'download metadata from server',
    Argument('-a', '--assignments', help='sync assignments', action='store_true'),
    Argument('-s', '--submissions', help='sync submissions', action='store_true'),
    Argument('-g', '--grades', help='sync grades', action='store_true'),
    Argument('-u', '--users', help='sync users', action='store_true', default=False),
    Argument('-f', '--files', help='sync file metadata', action='store_true', default=False)
)
def fetch(assignments=False, submissions=False, grades=False, users=False, files=False):
    #frontend = MoodleFrontend(config=get_global_config())

    sync_all = not any([users,submissions,assignments,grades,files])
    wt = Context.get_work_tree()
    course_ids = list(wt.meta.courses.values())

    if assignments or sync_all:
        print('syncing assignments… ', end='', flush=True)
        output = sync_assignments()
        print('finished. ' + ' '.join(output))

    if submissions or sync_all:
        print('syncing submissions… ', end='', flush=True)
        output = sync_submissions()
        print('finished. ' + ' '.join(output))

    if grades or sync_all:
        print('syncing grades… ', end='', flush=True)
        output = sync_grades()
        print('finished. ' + ' '.join(output))

    if users or sync_all:
        print('syncing users…', end=' ', flush=True)
        output = sync_users()
        print(output + 'finished.')

    if files:  # TODO: when finished, add 'or sync_all'
        print('syncing files… ', end='', flush=True)
        sync_file_meta_data()
        print('finished')




def sync_assignments():
    course_ids = list(Context.get_work_tree().meta.courses.keys())
    response = Context.get_session().mod_assign_get_assignments(course_ids)
    wrapped = responses.mod_assign_get_assignments(**response)
    result = Context.get_work_tree().meta.assignments.update(wrapped)
    output = ['{}: {:d}'.format(k, v) for k, v in result.items()]
    return output

def sync_users():
    # limit collected information to only relevant bits. is faster and can possibly work around some moodle bugs.
    sync_fields = ['fullname', 'groups', 'id']
    options = {'userfields': ','.join(sync_fields)}

    output = ""
    wt = Context.get_work_tree()
    for cid in wt.meta.courses:
        try:
            response = Context.get_session().core_enrol_get_enrolled_users(course_id=cid, options=options)
            for user in responses.core_enrol_get_enrolled_users(response):
                wt.meta.users[user.id] = user
            output += f'{cid:5d}:got {len(response):4d}\n'
        except AccessDenied as denied:
            message = f'{cid:d} denied access to users: {denied}\n'
            output += message
        except InvalidResponse as e:
            message = f'Moodle encountered an error: msg:{e.message} \n debug:{e.debug_message}\n'
            output += message

    return output

def sync_submissions():
    now = math.floor(datetime.now().timestamp())
    wt = Context.get_work_tree()
    response = Context.get_session().mod_assign_get_submissions(list(wt.meta.assignments),
                                                       since=wt.meta.submissions.last_sync)
    result = wt.meta.submissions.update(response, now)
    output = ['{}: {:d}'.format(k, v) for k, v in result.items()]
    return output

def sync_grades():
    now = math.floor(datetime.now().timestamp())
    wt = Context.get_work_tree()
    response = Context.get_session().mod_assign_get_grades(list(wt.meta.assignments), since=wt.meta.grades.last_sync)
    result = wt.meta.grades.update(response, now)
    output = ['{}: {:d}'.format(k, v) for k, v in result.items()]
    return output



parse_args_from_url = re.compile(r'.*pluginfile.php'
                                 r'/(?P<context_id>[0-9]*)'
                                 r'/(?P<component>\w+)'
                                 r'/(?P<file_area>\w+)'
                                 r'/(?P<item_id>[0-9]*).*')


def file_meta_dict_from_url(url):
    """
    parse the url into it's components, to use with core_files_get_files
    :param url: of the form:
    https://[HOST]/webservice/pluginfile.php/[contextid:int]/[component:str]/[filearea:str]/[item_id:int]/file.zip
    :return: a dict with the context id, componen, file area and item id
    {
        'context_id': '248648',
        'component': 'assignsubmission_file',
        'file_area': 'submission_files',
        'item_id': '505952'
    }

    """
    match = parse_args_from_url.match(url)
    return match.groupdict()


def sync_file_meta_data(self):
    files = []
    for as_id, submissions in self.wt.meta.submissions.items():
        for submission in submissions:
            for file in self.find_submission_files(submission):
                files.append(file)
                print(file)
                print(file_meta_dict_from_url(file.fileurl))
        with cf.ThreadPoolExecutor(max_workers=Context.MAX_WORKERS) as tpe:
            try:
                future_to_file = {tpe.submit(self.session.core_files_get_files, **file_meta_dict_from_url(file.fileurl)): file for file in files}
                for future in cf.as_completed(future_to_file):
                    file = future_to_file[future]
                    result = future.result()
                    print(result)
                    response = responses.core_files_get_files(**result)
                    for file in response.files:
                        print(file)
            except KeyboardInterrupt:
                print('stopping…')
                tpe.shutdown()
                raise

    # for file in files:
    #     wrapped = models.FileMetaDataResponse(self.session.core_files_get_files(**file.meta_data_params))
    #     print(str(wrapped.raw))
    #     for received in wrapped.files:
    #         print(received.author)

        # reply = moodle.get_submissions_for_assignments(wt.assignments.keys())
        # data = json.loads(strip_mlang(reply.text))
        # result = wt.submissions.update(data)
        # output = ['{}: {:d}'.format(k, v) for k, v in result.items()]
        # print('finished. ' + ' '.join(output))
