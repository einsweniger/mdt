import sys
from pathlib import Path
from . import strained, raw, siteinfo, siteinfofunctions
from bs4 import BeautifulSoup
from code import interact
import json

def extract_commands(soup):
    divs = list(soup.find_all(attrs={'class': 'collapsibleregion collapsed'}))
    while divs:
        yield divs.pop(0).extract()


def main(top_folder: Path, in_file: Path):
    # site_reported_functions_file = top_folder / siteinfofunctions
    # reported_functions = json.loads(site_reported_functions_file.read_text())
    # reportedset = set([d['name'] for d in reported_functions])  # make a list of all functions reported by the webservice
    # docset = set()

    soup = BeautifulSoup(in_file.read_text(), 'html.parser')
    for command in extract_commands(soup):
        nametag = command.findNext('div', class_='collapsibleregioncaption')
        name = nametag.text.strip()  # mod_lesson_get_pages
        splits = name.split('_')
        parent = top_folder / splits[0]  # mod
        if not parent.is_dir():
            parent.mkdir()
        outfolder = parent / splits[1]  # lesson
        if not outfolder.is_dir():
            outfolder.mkdir()
        file = outfolder / (name + '.html')
        file.write_text(str(command))
        # docset.add(nametag.text.strip())
    interact(local=locals())
    # print(soup)


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
    main(folder,file)