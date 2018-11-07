from bs4 import Tag, NavigableString
from code import interact


def is_empty(tag: Tag):
    return len(list(tag.children)) == 0


def clear_empty_text_elements(tag: Tag):
    children = list(tag.children)
    for child in children:
        if type(child) is NavigableString:
            if child.strip() == '':
                child.extract()



def extract_all_next_siblings(tag: Tag):
    things = list(tag.next_siblings)
    while things:
        thing = things.pop(0)
        yield thing.extract()


def clear_all_child_tags(container: Tag, tag_name):
    children = list(container.children)
    for child in children:
        if type(child) is Tag and child.name == tag_name:
            child.extract()


def strip_outer_div(tag: Tag):
    inner = tag.div.extract()
    clear_empty_text_elements(tag)
    if not is_empty(tag):
        interact(banner='there were more children than expected', local=locals())
    return inner


def is_not_br_tag(tag: Tag):
    if type(tag) is not Tag:
        return True
    return tag.name != 'br'


def is_not_div_tag(tag: Tag):
    if type(tag) is not Tag:
        return True
    return tag.name != 'div'


def is_not_empty_string(tag: Tag):
    if type(tag) is Tag:
        return True
    if type(tag) is not NavigableString:
        interact(banner='tag is not NavString', local=locals())
    return '' != tag.strip()



