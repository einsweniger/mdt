from . import pm, Argument, ArgumentGroup

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

    def determine_text_format_id(file_name):
        ending = file_name.split('.')[-1]
        if 'md' == ending:
            return text_format['markdown']
        if 'html' == ending:
            return text_format['html']
        if 'txt' == ending:
            return text_format['plain']
        return 0

    frontend = MoodleFrontend()
    file_item_id = 0
    if files is not None:
        file_response = frontend.upload_files(files)
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
        text_file_response = frontend.upload_files(textfiles)
        text_file_item_id = text_file_response[0]['itemid']

    submission_text = ''
    submission_text_format = 0
    if text is not None:
        submission_text = text.read()
        submission_text_format = determine_text_format_id(text.name)

    assignments = []
    if assignment_id is None:
        wt = WorkTree()
        for data in wt.assignments.values():
            assignments.append(Assignment(data))
        choice = interaction.input_choices_from_list(assignments, 'which assignment? ')
        assignment_id = assignments[choice[0]].id

    # print('{:s} {:d} {:d} {:d}'.format(text, submission_text_format, text_file_item_id, file_item_id))
    data = frontend.save_submission(assignment_id, submission_text, submission_text_format, text_file_item_id,
                                    file_item_id)
    print(data)

