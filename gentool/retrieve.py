import json

import requests
import re
from pathlib import Path

from bs4 import BeautifulSoup
from bs4 import SoupStrainer

from . import strained, raw, siteinfo, siteinfofunctions
url = 'https://demo.moodle.net'
ws_apidoc = '/admin/webservice/documentation.php'
ws_path = '/webservice/rest/server.php'
login_uri = '/login/index.php'
token_uri = '/login/token.php'

logindata = {'username': 'admin', 'password': 'sandbox'}
token_data ={'username': 'admin', 'password': 'sandbox', 'service': 'moodle_mobile_app'}
info_data ={'wstoken': None, 'wsfunction': 'core_webservice_get_site_info', 'moodlewsrestformat': 'json'}

release_re = re.compile(r'[0-9.]+')  # match everything that is numbers and dots within "3.5.2+ (Build: 20181016)"


def get_site_info(session):
    # get token
    token = session.post(url+token_uri, data=token_data).json()
    info_data.update({'wstoken': token['token']})
    return session.post(url+ws_path, data=info_data).json()

def make_output_path(release_info):
    version = release_re.match(release_info).group()
    major_minor = version[0:3]  # use the '3.5' part of '3.5.2'

    outfolder = Path.cwd() / f'api_{major_minor.replace(".","_")}'
    if not outfolder.is_dir():
        outfolder.mkdir()
    return outfolder


def main():
    # outfile = Path.cwd() / '3.5.html'

    # if outfile.is_file():
    #     main_soup = BeautifulSoup(outfile.read_text(), 'html.parser', parse_only=main_strain)
    #     # parse_api(main_soup)
    #     return

    s = requests.Session()

    # get session cookies
    r = s.post(url + login_uri, data=logindata)

    site_info = get_site_info(s)
    outfolder = make_output_path(site_info['release'])  # output folder will be: "api_3_5" (major, minor version)

    # pop out functions
    supported_functions = site_info.pop('functions')
    site_info_path = outfolder / siteinfo
    site_info_path.write_text(json.dumps(site_info, ensure_ascii=False, indent=2))

    function_path = outfolder / siteinfofunctions
    function_path.write_text(json.dumps(supported_functions, ensure_ascii=False, indent=2))

    # get api documentation
    r = s.get(url + ws_apidoc)
    raw_info_file = outfolder / raw
    raw_info_file.write_text(r.text)

    # use filter to only retrieve the interesting parts
    strainer = SoupStrainer(id='region-main')
    soup = BeautifulSoup(r.text, 'html.parser', parse_only=strainer)
    filtered_file = outfolder / strained
    filtered_file.write_text(str(soup))


if __name__ == '__main__':
    main()