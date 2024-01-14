#! /usr/bin/env python3

import os
import sys
import argparse
import logging
from pathlib import Path
import shutil

from url_parser import get_url

from sites import Site, STATS
from utils import validate_url, export


logging.basicConfig(filename='export/process.log', level=logging.ERROR, filemode='w')
logger = logging.getLogger(__name__)

    
def main(url, **kwargs):
    base_dir = os.getcwd()
    export_dir = os.path.join(base_dir, 'exports')
    sitename = get_url(url).domain
    location = os.path.join(export_dir, sitename)


    if Path(export_dir).exists():
        shutil.rmtree(export_dir)
    Path(export_dir).mkdir(parents=True, exist_ok=True,mode=0o777)
    Path(location).mkdir(parents=True, mode=0o777, exist_ok=True)
    os.chdir(location)

    site = Site(url, export_dir=export_dir, **kwargs)
    site.clone()
    os.chdir(base_dir)

    print('\n\n')
    print(f'Pages Downloaded: {STATS["pages"]}')
    print(f'Static Assets Downloaded: {STATS["assets"]}')
    print(f'Errors Encountered: {STATS["errors"]}')
    print("\n\n")

    print(f"Exporting site to {sitename}.zip ...")
    shutil.make_archive(sitename, format='zip', root_dir=export_dir)
    shutil.rmtree(location)
    print(f"site exported successfully\n\n")
    

    # return zipped


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='pyclone', description='Clones a website given the url')
    parser.add_argument('url', help='The link to the website you want to clone')
    # parser.add_argument('--filter',
    #     required=False,
    #     type=str,
    #     default='all',
    #     choices=['all', 'images', 'static', 'cssjs']
    #     help='Download only static files'
    # )
    parser.add_argument('--user', required=False, help='The username or password to use for authentication')
    parser.add_argument('--password', required=False, help='Password for basic authentication')
    parser.add_argument('--images-only', required=False, default=False, help='Download images only')

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
    sys.exit(0)