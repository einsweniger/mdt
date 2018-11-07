import re
from bs4 import NavigableString, Tag
from gentool.parser_utils import util
from gentool.parser_utils.general_structure import parse_general_structure
from code import interact


def wrangle_arguments(extracted_elements):
    result = []
    for arg in extracted_elements:
        children = list(arg.children)

        if len(children) != 9:
            interact(banner='arg does not have 9 elements', local=locals())

        if type(children[0]) != Tag or arg.name == 'b':
            interact(banner='child[0] was not b Tag', local=locals())

        if any([type(children[num]) is not NavigableString for num in (1, 3)]):
            interact(banner='child[1,3] was not NavString', local=locals())

        if any([util.is_not_br_tag(children[num]) for num in (2, 4, 5)]):
            interact(banner='child[2,4,5] was not br Tag', local=locals())

        if any([util.is_not_div_tag(children[num]) for num in (6, 7, 8)]):
            interact(banner='child[6,7,8] was not div Tag', local=locals())

        name =                children[0]
        annotation =          children[1]
        br =                  children[2]
        description =         children[3]
        br =                  children[4]
        br =                  children[5]
        general_structure =   children[6]  # yellow box
        php_structure =       children[7]  # green box
        post_parameters =     children[8]  # red box

        name = name.text.strip()
        annotation = parse_annotation(annotation)
        description = description.strip('\xa0')
        kind, structure = parse_general_structure(general_structure)
        result.append({
            'name': name,
            'annotation': annotation,
            'description': description,
            'kind': kind,
            'structure': structure,
            # 'php_structure': php_structure,
            # 'post_parameters': post_parameters,
        })
        # if type(general_structure) is tuple:
        #     interact(banner='check general_structure, is tuple', local=locals())
    return result


default_matcher = re.compile(r'\(Default to "(.*)"\)', flags=re.S)


def parse_annotation(text):
    stripped = text.strip()
    if '(Required)' == stripped:
        return {'required': True}
    if '(Optional)' == stripped:
        return {'required': False}

    match = default_matcher.match(stripped)
    if match is None:
        interact(banner=f'match could not match: {stripped}', local=locals())
    default_value = match.group(1).replace('\n', '')
    # interact(banner=f'match: {default_value}', local=locals())
    return {'default': default_value}



