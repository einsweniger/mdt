from util import interaction
from . import pm, Argument, ArgumentGroup
import argparse
from enum import IntEnum
from pathlib import Path
from mdt import Context
from moodle.responses import FileUploadResponse, MoodleAssignment


class text_format(IntEnum):
    moodle = 0
    html = 1
    plain = 2
    markdown = 4

@pm.command(
    'submit text or files to assignment for grading',
    Argument('-a', '--assignment_id', help='the assignment id to submit to.'),
    ArgumentGroup('online', 'for online text submission', [
        Argument('-tf', '--textfiles', nargs='+', type=argparse.FileType('rb'),
                 help='files you want in the text. pictures in markdown?'),
        Argument('-t', '--text', type=argparse.FileType(),
                 help='the text file with content you want to submit (txt,md,html)')
    ]),
    ArgumentGroup('files', 'for file submission', [
        Argument('-f', '--files', nargs='+', type=argparse.FileType('rb'), help='the files you want to sumbit.')
    ])
)
def submit(text=None, textfiles=None, files=None, assignment_id=None):
    """ Bei nur Datei Abgabe, keine File ID angegeben. [
    {
    "item": "Es wurde nichts eingereicht.",
    "itemid": 4987,
    "warningcode": "couldnotsavesubmission",
    "message": "Could not save submission."
    }
    ]"""

    file_item_id = 0
    if files is not None:
        file_response = upload_files(files)
        if file_response.has_errors:
            for error in file_response.errors:
                print(error)
            answer = input('errors occured, continue anyway? [Y/n]: ')
            if 'n' == answer:
                raise SystemExit(0)
            elif not ('y' == answer.lower() or '' == answer):
                print('wat')
                raise SystemExit(1)
        for file in file_response:
            file_item_id = file.item_id
            break

    text_file_item_id = 0
    if textfiles is not None:
        text_file_response = upload_files(textfiles)
        text_file_item_id = text_file_response[0]['itemid']

    submission_text = ''
    submission_text_format = 0
    if text is not None:
        submission_text = text.read()
        submission_text_format = determine_text_format_id(text.name)

    assignments = []
    if assignment_id is None:
        wt = Context.get_work_tree()
        for data in wt.meta.assignments.values():
            assignments.append(MoodleAssignment(**data))
        choice = interaction.input_choices_from_list(assignments, 'which assignment? ')
        assignment_id = assignments[choice[0]].id

    # print('{:s} {:d} {:d} {:d}'.format(text, submission_text_format, text_file_item_id, file_item_id))
    data = save_submission(assignment_id, submission_text, submission_text_format, text_file_item_id,
                                    file_item_id)
    print(data)


def determine_text_format_id(file_name: Path) -> IntEnum:
    ending = file_name.suffix
    if 'md' == ending:
        return text_format.markdown
    if 'html' == ending:
        return text_format.html
    if 'txt' == ending:
        return text_format.plain
    return text_format.moodle


def upload_files(files):
    # TODO, Wrap and return it, don't print. do print in wstools.upload. also modify submit
    response = Context.get_session().upload_files(files)
    return FileUploadResponse(**response)


def save_submission(assignment_id, text='', text_format=0, text_file_id=0, files_id=0):
    # TODO: wrap and return to wstools.submit
    response = Context.get_session().mod_assign_save_submission(assignment_id, text, int(text_format), text_file_id, files_id)
    return response
