#! /usr/bin/env python3

import os
import sys
import argparse
import logging
from io import BytesIO
import requests
from pathlib import Path
from collections import deque
from typing import List

from url_parser import parse_url

from generator import Generator
from clone import Page
from urls import Link, validate_url
from exceptions import PageNotFoundError
from transform import make_relative

logging.basicConfig(filename='export/process.log', level=logging.ERROR, filemode='w')
logger = logging.getLogger(__name__)

EXPORT_PATH = Path('export')
MAX_PAGES = 50
STATS = {
    'pages': 0,
    'assets': 0,
    'errors': 0
}

class Clone:
    '''A class that crawls a website and create a static equivalent
    
    ...
    
    Attributes
    ----------
    base_url (str)
        the base url of the target website
    visited_paths (list)
        list of paths which have been created
    static_assets (set)
        The list of static assets from the site
    site_pages(list)
        A queue of all the site pages to avoid visiting twice
    '''

    def __init__(self, base_url, user: str=None, password:str = None) -> None:
        '''initializes an instance with a base_url'''
        self.base_url = base_url
        self.session = requests.session()
        if user:
            self.session.auth = (user, password)

        self.visited_paths = []
        self.static_assets = set()
        self.site_links: List[Link] = deque()
        self.site_links.append(
            Link('/', link_type=Link.LinkType.ABSOLUTE, page_url=base_url)
        )
    

    def create_path(self, path: str, content: BytesIO, overwrite: bool = False):
        '''creates a file path in the export directory'''
        if  not Path(path).exists() or overwrite:
            if '/' in path:
                dir, filename = path.rsplit('/', maxsplit=1)
                Path(dir).mkdir(parents=True, exist_ok=True,mode=0o777)
            else:
                filename = path
            with open(path, 'wb') as new:
                new.write(content)
            return path
        logging.info(f'{path} already exists')
        return f'** {path} already exists'

    def download(self, url: str):
        '''downloads the asset pointed to by the link'''
        response = self.session.get(url, allow_redirects=True, timeout=10)
        if response.status_code == 404:
            raise PageNotFoundError(f'Page does not exist: {url}')

        file = response.content

        path = parse_url(url)['path'].lstrip('/')
        if path:
            return self.create_path(path=path, content=file)

    def get_page(self, link):
        '''gets a html page from a url endpoint'''
        response = self.session.get(link, allow_redirects=True, timeout=10)
        if response.status_code == 404:
            raise PageNotFoundError(f'Page does not exist: {link}')

        return response.content
    
    def get_static(self, page: str, page_url: str):
        '''parses a html page and returns a list of all the static assets'''
        generator = Generator(page, page_url=page_url, base_url=self.base_url)
        css = generator.generate_css()
        js = generator.generate_js()
        images = generator.generate_images()
        assets = css + js + images       
        for asset in assets:
            if str(asset) not in self.static_assets:
                self.static_assets.add(str(asset))

    def get_site_pages(self):
        '''downloads all the static pages
        then adds all the static files to ``static_assets``,
        queue all the unprocessed site links for further
        processing
        '''
        while len(self.site_links) and len(self.visited_paths) < MAX_PAGES:
            link = self.site_links.pop()
            print(f'** {link}')
            
            if not validate_url(str(link), check_if_exist=False):
                logger.error(f'Badly formed URL: {str(link)}')
                continue

            try:
                page = self.get_page(str(link))
                self.get_static(page, page_url=str(link))
                path = link.url_to_path()
                
                self.visited_paths.append(path)
                g = Generator(page, page_url=link.normalize(), base_url=self.base_url)
                tranforms_dict = g.get_transforms()
                # print(tranforms_dict)
                page = make_relative(page, transforms=tranforms_dict)
                self.create_path(path=path, content=page)

                links = g.generate_links()
                for link in links:
                    if link.url_to_path() not in self.visited_paths and link not in self.site_links:
                        self.site_links.append(link)
            except:
                STATS['errors'] += 1
                logger.exception(f'--failed {str(link)}')
            else:
                STATS['pages'] += 1

        
def main(url, **kwargs):
    site = Clone(url, **kwargs)

    print('\n*******  Generating site pages  ******\n')

    EXPORT_PATH.mkdir(parents=True, mode=0o777, exist_ok=True)
    os.chdir(EXPORT_PATH)

    site.get_site_pages()
    
    print(('\n*******  Downloading static files  ******\n'))
    
    for asset in site.static_assets:
        print(f'++ {asset}')
        try:
            if validate_url(asset, check_if_exist=False):
                site.download(asset)
            else:
                logger.error(f'Badly formed url: {asset}')
        except:
            STATS['errors'] += 1
            logger.exception('  -- failed')
        else:
            STATS['assets'] += 1

    print('\n' * 2)
    print(f'Pages Downloaded: {STATS["pages"]}')
    print(f'Static Assets Downloaded: {STATS["assets"]}')
    print(f'Errors Encountered: {STATS["errors"]}')


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
    
    main(url, **params)