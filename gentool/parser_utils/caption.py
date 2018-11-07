from code import interact
from bs4 import Tag
from .util import is_empty, clear_empty_text_elements


def extract_caption(soup: Tag):
    caption_div = soup.findNext('div', class_='collapsibleregioncaption')
    if not caption_div.strong:
        interact(banner='caption contains no strong element', local=locals())
    strong = caption_div.strong.extract()
    # there are more seperated spaces in there, so we clear the empty text
    clear_empty_text_elements(caption_div)

    # then check if we missed something
    if not is_empty(caption_div):
        interact(banner='caption contains more elements', local=locals())
    # otherwise remove is from the parent
    caption_div.extract()
    return strong.text.strip()
