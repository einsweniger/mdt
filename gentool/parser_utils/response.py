from code import interact
from bs4 import Tag, NavigableString
from gentool.parser_utils import util
from gentool.parser_utils.general_structure import parse_general_structure


def wrangle_response(response):
    response = list(response.children)
    if len(response) == 0:
        return None
    if len(response) == 6:
        response = response[3:]
    if len(response) != 3:
        interact(banner='response does not have 3 elements', local=locals())

    if any([util.is_not_div_tag(response[num]) for num in (0,1,2)]):
        interact(banner='child[6,7,8] was not div Tag', local=locals())

    general_structure =   response[0]  # yellow box
    php_structure =       response[1]  # green box
    post_parameters =     response[2]  # red box

    general_structure = parse_general_structure(general_structure)
    # interact(banner='check general_structure', local=locals())
    return general_structure