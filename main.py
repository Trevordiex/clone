#! /usr/bin/env python3

import os
import sys
import argparse
import logging
from pathlib import Path

from sites import Site, STATS
from utils import validate_url


logging.basicConfig(filename='export/process.log', level=logging.ERROR, filemode='w')
logger = logging.getLogger(__name__)

    
def main(url, **kwargs):
    export_dir = Path('exports')
    export_dir.mkdir(parents=True, mode=0o777, exist_ok=True)
    os.chdir(export_dir)

    site = Site(url, export_dir=export_dir, **kwargs)
    zipped = site.clone()

    print('\n' * 2)
    print(f'Pages Downloaded: {STATS["pages"]}')
    print(f'Static Assets Downloaded: {STATS["assets"]}')
    print(f'Errors Encountered: {STATS["errors"]}')

    return zipped


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='pyclone', description='Clones a website given the url')
    parser.add_argument('url', help='The link to the website you want to clone')
    parser.add_argument('--user', required=False, help='The username or password to use for authentication')
    parser.add_argument('--password', required=False, help='Password for basic authentication')

    arguments = parser.parse_args()
    url = arguments.url
    params = {}
    if (arguments.user or arguments.password) and not (arguments.user and arguments.password):
        sys.exit('user or password missing in authentication credentials')
    else:
        params['user'] = arguments.user
        params['password'] = arguments.password

    if not validate_url(url, check_if_exist=True):
        sys.exit('URL failed validation')

    file = main(url, **params)
    print(file)
    sys.exit(0)