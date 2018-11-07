import sys
from pathlib import Path
from . import strained, raw, siteinfo, siteinfofunctions
from bs4 import BeautifulSoup, Tag, NavigableString
from code import interact
from gentool.parser_utils.util import is_empty, strip_outer_div, clear_all_child_tags
from gentool.parser_utils.caption import extract_caption
from gentool.parser_utils.method_splitter import extract_main_sections
import json


def find_folders(folder: Path):
    for path in folder.iterdir():
        if path.is_dir():
            yield path


def find_html(folder: Path):
    for path in folder.iterdir():
        if path.is_file() and path.suffix == '.html':
            yield path


def find_function_files(root: Path):
    for folder in find_folders(root):
        for subfolder in find_folders(folder):
            yield from find_html(subfolder)


def extract_method_description(inner: Tag):
    # there are two more empty containers around the data
    inner = strip_outer_div(inner)
    inner = strip_outer_div(inner)
    clear_all_child_tags(inner, 'br')
    # now there is another empty div
    inner = strip_outer_div(inner)
    description = inner.next.extract()
    if type(description) is not NavigableString:
        interact(banner='description is not a string', local=locals())
    if not is_empty(inner):
        interact(banner='inner contains more elements!', local=locals())
    #interact(banner='check inner for more content', local=locals())
    return description


def main(root: Path):
    for path in find_function_files(root):
        funcname = path.stem
        print(funcname)
        inner = strip_outer_div(BeautifulSoup(path.read_text(), 'html.parser'))
        if not funcname == extract_caption(inner):
            interact(banner='funcname differs from caption', local=locals())

        sections = extract_main_sections(inner)
        sections['description'] = extract_method_description(inner)

        outpath: Path = path.parent / (funcname + '.json')
        outpath.write_text(json.dumps(sections, ensure_ascii=False, indent=2))
        #interact(banner='check outpath', local=locals())


if __name__ == '__main__':
    try:
        api_folder = str(sys.argv[1])
    except KeyError:
        print('please provide the folder of the retreived documentation as parameter')
        raise SystemExit(1)
    folder = Path(api_folder)
    if not folder.is_dir():
        raise SystemExit(f'no such directory {folder}')

    file = folder / strained
    if not file.is_file():
        raise SystemExit(f'no such file {file}')
    main(folder)
