from . import pm, Argument
from urllib.parse import urlparse, parse_qs
from typing import Tuple

def parse_or_throw(url) -> Tuple[str, str, int]:
    errmsg = f"""
    this does not seem to be a URL to a course, 
    I expected something like: https://moodle.uni-ulm.de/course/view.php?id=10428
    but you entered: {url}
    """

    p = urlparse(url)
    print(p)
    if '/course/view.php' != p.path:
        raise ValueError(errmsg)

    params = parse_qs(p.query)
    try:
        ids = params.get('id')
        if len(ids) != 1:
            raise ValueError(errmsg)
        string = ids.pop()
        id = int(string)

    except KeyError:
        raise ValueError(errmsg)
    except ValueError:
        raise ValueError(f'expected id to be an integer, but it was {string}')

    return p.scheme, p.hostname, id

@pm.command(
    'get a course to work with, locally',
    Argument('url', help='the URL of the moodle course'),
    Argument('folder', help='the name of the created folder', nargs='?')
)
def clone(url, folder=None):
    scheme, host, course = parse_or_throw(url)
    base_url = f'{scheme}://{host}'

