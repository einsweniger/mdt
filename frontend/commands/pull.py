from mdt import Context
from persistence.worktree import WorkTree
from . import pm, Argument
from util import interaction, zipwrangler

from concurrent import futures
from typing import List
import re
from pathlib import Path
from moodle.responses import MoodleSubmission, MoodleAssignment, MoodleUser
from pprint import pprint
import os

def safe_file_name(name):
    return re.sub(r'\W', '_', name)


def create_folders(files):
    folders = set([f.path.parent for f in files])
    for folder in folders:
        folder.mkdir(exist_ok=True, parents=True)


def collect_submission_files(sub: MoodleSubmission):
    for plug in sub.plugins:
        for fa in plug.fileareas:
            for file in fa.files:
                yield file


@pm.command(
    'retrieve files for grading',
    Argument('assignment_ids', nargs='*', type=int),
    Argument('--all', help='pull all due submissions, even old ones', action='store_true')
)
def pull(assignment_ids=None, all=False):
    wt = WorkTree()

    outpath2url = []
    for aid in wt.meta.submissions:
        assignment_folder = wt.get_folder_for_assignment(aid)
        print(assignment_folder)
        assignment = MoodleAssignment(**wt.meta.assignments[aid])
        grade_file_content = []
        for submission_data in wt.meta.submissions[aid]:
            out_folder = assignment_folder
            submission = MoodleSubmission(**submission_data)
            files = list(collect_submission_files(submission))
            if len(files) == 0:
                continue

            user: MoodleUser = wt.meta.users[submission.userid]
            if len(files) > 1:
                out_folder = assignment_folder / safe_file_name(user.fullname)

            for file in files:
                path = Path(file.filename)
                outpath = out_folder / (safe_file_name(user.fullname) + path.suffix)
                if outpath.is_file():
                    stat = outpath.stat()

                    if file.timemodified > stat.st_mtime:
                        outpath2url.append((outpath, file))
                else:
                    outpath2url.append((outpath, file))

            if assignment.teamsubmission:
                # TODO get one userid of the group
                return
            if submission.status == 'submitted' and submission.gradingstatus == 'notgraded':
                grade = 0.0
                line = f'{{"name": "{user.fullname:20}", "uid": {user.id:5d}, "grade": {grade:3.1f}, "feedback":"" }}'
                grade_file_content.append(line)

        filecontent = f'{{"assignment": {aid:d}, "team":{assignment.teamsubmission}, "grades": [\n'
        filecontent += ',\n'.join(sorted(grade_file_content)) + '\n]}'
        print(filecontent)
        counter = 0
        grade_file_path = assignment_folder / f'grades_{counter:02d}.json'
        while grade_file_path.is_file():
            counter += 1
            grade_file_path = assignment_folder / f'grades_{counter:02d}.json'
        grade_file_path.write_text(filecontent)
        download_files(outpath2url)




    #for a in assignments:
    #    wt.write_grading_and_html_file(a)

def write_submission_file(path: Path, content, meta):
    path.write_bytes(content)
    # set the modification time of the file, so we can check against newer files reported by moodle
    os.utime(path, (0, meta.timemodified))
    if path.suffix == '.zip':
        # if the files are deleted, they will be redownloaded and the unpack fails
        # store the information about the download somewhere.
        zipwrangler.clean_unzip_with_temp_dir(path, target=path.parent, remove_zip=False)


def download_files(outpath2url):
    file_count = len(outpath2url)
    counter = 0
    session = Context.get_session()
    if file_count == 0:
        return
    interaction.print_progress(counter, file_count)
    with futures.ThreadPoolExecutor(max_workers=Context.MAX_WORKERS) as tpe:
        try:
            future_to_file = {tpe.submit(session.download_file, file.fileurl): (file, outpath) for outpath, file in outpath2url}
            for future in futures.as_completed(future_to_file):
                file, outpath = future_to_file[future]
                response = future.result()
                counter += 1
                interaction.print_progress(counter, file_count, suffix=outpath)
                write_submission_file(outpath, response.content, file)
        except KeyboardInterrupt:
            print('stopping…')
            tpe.shutdown()
            raise


def grading_file_content(a: MoodleAssignment):
    # TODO, instead of writing the submission.id, write the user.id instead.
    # TODO, add team_submission to the file, saves work when uploading grades.
    head = '{{"assignment_id": {:d}, "grades": [\n'
    end = '\n]}'
    line_format = '{{"name": "{}", "id": {:d}, "grade": {:3.1f}, "feedback":"" }}'
    content = []

    if a.teamsubmission:
        for s_id, s in a.submissions.items():
            if s.groupid not in self.course.groups:
                # FIXME: invalid grouping
                continue
            group = self.course.groups[s.groupid]
            grade = 0.0
            if s.grade is not None:
                grade = s.grade.value or 0.0

            line = f'{{"name": "{group.name}", "id": {s.id}, "grade": {grade:3.1f}, "feedback":"" }}'
            content.append(line)
    else:
        for s_id, s in self.submissions.items():
            user = self.course.users[s.userid]
            grade = 0.0
            if s.grade is not None:
                grade = s.grade.value or 0.0
            print(f'{user.name}')
            print(f'{s.id}')
            print(f'{grade}')
            line = f'{{"name": "{user.name}", "id": {s.id}, "grade": {grade:3.1f}, "feedback":"" }}'
            content.append(line)

    return head.format(self.id) + ',\n'.join(sorted(content)) + end