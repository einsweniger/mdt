from . import pm
from moodle import responses
from mdt import Context
import json
@pm.command(
    'dump course contents, work in progress'
)
def dump():
    wt = Context.get_work_tree()
    for course_id in wt.meta.courses:
        response = Context.get_session().core_course_get_contents(course_id)
        wrapped = responses.core_course_get_contents(response)
        for section in wrapped:
            for module in section.modules:
                """
                known modnames and how to dump:
                forum: via mod_forum_get_forum_discussions_paginated, to get discussion id list
                    then use mod_forum_get_forum_discussion_posts, to dump the posts.
                    posts can have attachments, download maybe?
                assign: is easy, already implemented.
                folder: can contain multiple files, the urls may contain the ?forcedownload parameter
                    which might need to get stripped, not quite sure
                resource: same as folder, both have 'contents' field, containing a fileurl, should check type.
                label: is just an annotation to an activity, so just dump description.

                uncertain:
                choice: has externallib, should be dumpable.
                page: presents html, has no externallib, cant be dumped via WS.
                    but page contains an url, can be downloaded, maybe.
                quiz: has externallib, but is not accessible to me.

                lesson,
                ratingallocate,
                label,
                wiki: no clue

                undumpable:

                lti: linked external learning tool, can't do anything about that.
                choicegroup: no externallib, https://github.com/ndunand/moodle-mod_choicegroup
                """
                # print(module.modname)
                known_dumpable = ['forum', 'assign', 'folder', 'resource', 'label']
                uncertain = ['choice', 'lesson', 'quiz', 'wiki', 'page', 'ratingallocate', 'publication']
                known_undumpable = ['lti', 'choicegroup']
                unchecked = ['url', 'organizer', 'checklist', 'glossary', 'feedback', 'book', 'attendance']

                if module.modname not in known_dumpable+uncertain+known_undumpable+unchecked:
                    print(module.modname)
                    #print(json.dumps(module.raw, indent=2, ensure_ascii=False))
                if module.modname == 'organizer':
                    print(json.dumps(module.raw, indent=2, ensure_ascii=False))

