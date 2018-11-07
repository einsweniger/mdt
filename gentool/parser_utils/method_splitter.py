from bs4 import Tag, NavigableString
from code import interact
from gentool.parser_utils.util import is_empty, extract_all_next_siblings, clear_all_child_tags, is_not_br_tag
from gentool.parser_utils.arguments import wrangle_arguments
from gentool.parser_utils.response import wrangle_response

expected_headlines = [
    'Arguments',
    'Response',
    'Error message',
    'Restricted to logged-in users',
    'Callable from AJAX'
]

""" Error message is always:
<?xml version="1.0" encoding="UTF-8"?>
<EXCEPTION class="invalid_parameter_exception">
    <MESSAGE>Invalid parameter value detected</MESSAGE>
    <DEBUGINFO></DEBUGINFO>
</EXCEPTION>

so we don't really care about it.
"""

def extract_main_sections(tag: Tag):
    # the main sections are not in seperated containers
    # so we look for their headlines ({'style': 'color:#EA33A6'})
    # then we use them in reverse order to top pop all children from the document
    headline_tags = list(tag.find_all(attrs={'style': 'color:#EA33A6'}))
    headline_texts = [e.text.strip() for e in headline_tags]
    if expected_headlines != headline_texts:
        interact(banner='the headings are not as expected', local=locals())
    result = dict()
    for name, heading in zip(reversed(headline_texts), reversed(headline_tags)):
        # extract all elements after the heading
        extracted_elements = list(extract_all_next_siblings(heading))
        # extract the heading and prepend it to the list
        head_span: Tag = heading.extract()
        # remove all breaks from the heading, just to be sure we extract all information
        clear_all_child_tags(head_span, 'br')
        text = head_span.next.extract()
        if type(text) is not NavigableString:
            interact(banner='the extracted text is no text, but something else', local=locals())
        if not text == name:
            interact(banner='this is not the heading we expected', local=locals())
        if not is_empty(head_span):
            interact(banner='head_span contains more elements', local=locals())

        # remove all br tags from  the list:
        extracted_elements = list(filter(is_not_br_tag, extracted_elements))
        if name in ('Error message', 'Response', 'Callable from AJAX', 'Restricted to logged-in users'):
            # exactly one element for all these sections
            if len(extracted_elements) != 1:
                interact(banner='extracted_elements contained something else than br and the span', local=locals())
            result[name] = extracted_elements[0]
        else:
            # Arguments has multiple elements
            result[name] = wrangle_arguments(extracted_elements)
    result['Response'] = wrangle_response(result['Response'])

    if 'Error message' in result:
        result.pop('Error message')

    return result

