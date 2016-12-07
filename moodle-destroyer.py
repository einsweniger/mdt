#!/usr/bin/env python

import sys
import csv
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog="Moodle Destroyer", prefix_chars="-")

    parser.add_argument("-d", "--destroy",
                        nargs=2,
                        required=True,
                        type=argparse.FileType('rU'),
                        help="grading-file, moodle-file, result-file")
    parser.add_argument("-r", "--result",
                        nargs=1,
                        required=False,
                        type=argparse.FileType('w'),
                        help="result-file")
    parser.add_argument("-s", "--single",
                        action="store_true",
                        default=False,
                        help="is in single mode")
    parser.add_argument("-f", "--feedback",
                        action="store_false",
                        default=True,
                        help="no feedback column in grading")
    parser.add_argument("-v", "--version",
                        action="version",
                        version="version 0.2.0")

    args = parser.parse_args()

    if args.destroy[0] is not None:
        GRADING_FILE = args.destroy[0].name
    else:
        raise Exception

    if args.destroy[1] is not None:
        MOODLE_EXPORT = args.destroy[1].name
    else:
        raise Exception

    if args.result[0] is not None:
        RESULT_FILE = args.result[0].name
    else:
        raise Exception

    with open(GRADING_FILE, 'rU', newline='') as grading, \
         open(MOODLE_EXPORT, 'rU', newline='') as moodle, \
         open(RESULT_FILE, 'w', newline='') as result:
        reader_grading = csv.DictReader(grading)
        reader_moodle = csv.DictReader(moodle)

        header = reader_moodle.fieldnames
        writer = csv.DictWriter(result,
                                header,
                                quotechar='"',
                                quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        moodlelist = []
        gradinglist = []

        for line in reader_moodle:
            moodlelist.append(line)
        for line in reader_grading:
            gradinglist.append(line)

        for line in gradinglist:
            for row in moodlelist:
                # print(line['Gruppe'],"\nrow:",row['Gruppe'])
                if args.single:
                    if line['Vollständiger Name'] == row['Vollständiger Name']:
                        row['Bewertung'] = line['Bewertung']
                        if args.feedback:
                            row['Feedback als Kommentar'] = line['Feedback als Kommentar']
                        writer.writerow(row)
                else:
                    if line['Gruppe'] == row['Gruppe']:
                        row['Bewertung'] = line['Bewertung']
                        if args.feedback:
                            row['Feedback als Kommentar'] = line['Feedback als Kommentar']
                        writer.writerow(row)
