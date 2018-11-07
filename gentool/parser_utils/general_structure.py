from gentool.parser_utils.parserstack import ResultSetEmitter
from gentool.parser_utils import util
from code import interact
from bs4 import Tag, NavigableString
import re



def parse_general_structure(tag: Tag):
    tag = util.strip_outer_div(tag)
    childs = list(filter(util.is_not_br_tag, tag.pre.children))
    childs = list(filter(util.is_not_empty_string, childs))
    head = childs.pop(0)
    if type(head) is not Tag or head.name != 'b' or head.text.strip() != 'General structure':
        interact(banner='assumption about head failed', local=locals())
    if len(childs) == 2:
        # 'fix' for tool_usertours_complete_tour
        if 'object {' == childs[0].strip() and childs[1].strip() == '}':
            return ('complex', {'type': 'object', 'default': {}})
        return ('simple', parse_simple_argument(*childs))
    return ('complex', parse_complex_argument(childs))
    # if len(childs) != 3:
    #     interact(banner='check childs', local=locals())


simple_default_matcher = re.compile(r'Default to "(.*)"', flags=re.S)
php_type_to_python = {
    'string': 'str',
    'int': 'int',
    'double': 'float'
}
complex_type_strings = ('list of (', 'object {', ')', '}')

def parse_description(annotation):
    if not annotation.i:
        return {}
    description = annotation.i.extract().text.strip()
    if not description.startswith('//'):
        interact(banner=f'this does not seem to be a description: {description}')
        return {}
    return {'description': description.replace('//', '')}


def parse_bold_text(annotation):
    bold_result = dict()
    if not annotation.b:
        return {}

    bold_text = annotation.b.extract().text.strip()

    if bold_text == 'Optional':
        return {'optional': True}

    match = simple_default_matcher.match(bold_text)
    if match is None:
        interact(banner='annotation had default, but no match', local=locals())
        return {}

    default = match.group(1).replace('\n', '')
    return {'default': default}


def parse_annotation_span(annotation: Tag):
    util.clear_empty_text_elements(annotation)

    result = dict()
    result.update(parse_description(annotation))
    result.update(parse_bold_text(annotation))

    if not util.is_empty(annotation):
        interact(banner=f'annotation has more content: {annotation}', local=locals())
    return result


def parse_simple_argument(tp, annotation):
    result = dict()

    tp = tp.replace('\n', '').strip()
    if tp not in php_type_to_python:
        interact(banner=f'unknown type encountered: {tp}', local=locals())
        tp = None
    else:
        result['type'] = php_type_to_python[tp]
        # tp = php_type_to_python[tp]

    result.update(parse_annotation_span(annotation))

    # interact(banner=f'{annotation}', local=locals())
    return result


def tokenize(childs):
    new_childs = []
    while childs:
        thing = childs.pop(0)
        if type(thing) is not NavigableString:
            new_childs.append(thing)
            continue
        stripped = thing.strip()

        if stripped in complex_type_strings:
            new_childs.append(stripped)
            continue

        if stripped in php_type_to_python:
            new_childs.append(stripped)
            continue

        if 'string }' == stripped:
            childs = stripped.split() + childs
            continue

        if set(list(stripped)) == set(list(')}')):
            childs = list(stripped) + childs
            continue

        if set(list(stripped)) == set(list(')')):
            childs = list(stripped) + childs
            continue

        if set(list(stripped)) == set(list('}')):
            childs = list(stripped) + childs
            continue

        interact(banner=f'something unexpected in parsed type info: {stripped}', local=locals())

    return new_childs


def parse_complex_argument(childs):
    parsed_first_annotation = None
    if type(childs[0]) is Tag:
        first = childs.pop(0)
        if first.name != 'span':
            interact(banner=f'first is tag but not span', local=locals())
            util.clear_empty_text_elements(first)
        parsed_first_annotation = parse_annotation_span(first)
        # if 'default' in parsed_first_annotation:
        #     print(parsed_first_annotation)
        #
    if type(childs[0]) is not NavigableString:
        interact(banner=f'{childs}', local=locals())

    test_childs = tokenize(childs)
    rse = ResultSetEmitter()
    properties = None
    for c in test_childs:
        if type(c) is str:
            if 'list of (' == c:
                rse._on_array_start()
                continue
            if 'object {' == c:
                rse._on_object_start()
                continue
            if '}' == c:
                if properties is not None:
                    rse._on_value(properties)
                    properties = None
                rse._on_object_end()
                continue
            if ')' == c:
                if properties is not None:
                    if 'type' in properties:
                        tp = properties.pop('type')
                        properties.update({
                            'type': 'array',
                            'items': tp
                        })
                    rse._on_element(properties)
                    properties = None
                rse._on_array_end()
                continue
            if c in php_type_to_python:
                if properties is None:
                    properties = {'type': c}
                else:
                    properties.update({'type': c})
                continue
            interact(banner=f'missed something else: {c}', local=locals())
        if type(c) is Tag:
            if c.name == 'b':
                if properties is not None:
                    rse._on_value(properties)
                    properties = None
                rse._on_key(c.text.strip())
                continue
            if c.name == 'span':
                result = parse_annotation_span(c)
                if properties is None:
                    properties = result
                else:
                    properties.update(result)
                continue
            interact(banner=f'was not b or span', local=locals())
    # pprint(parsed_first_annotation)
    # pprint(rse.result)
    # interact(banner=f'done with new parser', local=locals())
    return parsed_first_annotation, rse.result
