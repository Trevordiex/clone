#! /usr/bin/env python3

import os
import logging
import requests
from pathlib import Path
from collections import deque
from typing import List, Mapping

from url_parser import get_url

from generator import Parser
from models import Link, find_urls
from exceptions import PageNotFoundError, FileAlreadyExists, AuthenticationError
from utils import save_file, make_relative, validate_url, make_byte

logging.basicConfig(filename='process.log', level=logging.ERROR, filemode='w')
logger = logging.getLogger(__name__)

EXPORT_PATH = Path('export')
MAX_PAGES = 50
STATS = {
    'pages': 0,
    'assets': 0,
    'errors': 0
}

class Page:
    def __init__(self, url: Link, session, *, base_url, **kwargs):
        '''A webpage model'''
        self.url = str(url)
        self.link = url
        self.base_url = base_url
        self.session = session
        self._content = self.get(self.url, session=session)
        self.parser = Parser(html=self._content, page_url=self.url, base_url=self.base_url)
        self.transforms = {}
    
    @staticmethod
    def get(url: str, session=None):
        '''downloads the asset pointed to by the link'''
        response = session.get(url, allow_redirects=True, timeout=10)
        if response.status_code == 404:
            raise PageNotFoundError(f'Page does not exist: {url}')
        elif response.status_code == 403:
            raise AuthenticationError('Authentication or Authorization failure')

        return response.content

    def get_images(self):
        return self.parser.get_images()

    def get_media(self):
        return self.parser.get_media()

    def get_links(self):
        return self.parser.get_links()
    
    def get_cssjs(self):
        return self.parser.get_cssjs()

    def download(self):
        try:
            path = self.link.relative
            filename = save_file(path, self.content)
        except FileAlreadyExists:
            return False
        except TypeError:
            print(f'TypeError: File could not be saved <{path}>', self.content)
            return False
        return filename

    @property
    def content(self):
        '''make all the page links relative'''
    
        links = [*self.get_links(), *self.get_cssjs(), *self.get_images(), *self.get_media()]
        rcontent = self._content[:]
        print(type(rcontent))
        for link in links:
            rcontent = rcontent.replace(make_byte(link.link), make_byte(link.relative))
        return rcontent


class Site:
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

    def __init__(
            self,
            base_url,
            /,
            user: str=None,
            password:str = None,
            images_only: bool = False,
            include_media: bool = False,
            single_page: bool = False,
            *args,
            **kwargs
        ) -> None:
        '''initializes an instance with a base_url'''
        self.base_url = base_url
        self.session = requests.session()
        self.images_only = images_only
        self.include_media = include_media
        self.single_page = single_page
        if user:
            self.session.auth = (user, password)
        self.sitename = get_url(self.base_url).domain

        self.pages: Mapping[str: Page] = {}             # A mapping of already processed links to actual page content
        self.visited_paths: List[str] = []              # A list of already visited links
        self.site_links: List[Link] = deque()           # List of site links in a queue

        self.images = set()                             # All the images to download in a set
        self.cssjs = set()                              # all the cssjs to download in a set
        self.media = set()                              # Media links to download in a set
        self.extra_links = set()                        # Links parsed from other assets
        self.visited_links: List[str] = []              # A list of downloaded assets


    @property
    def assets(self) -> List[Link]:
        return {*self.images, *self.cssjs, *self.media}

    def clone(self):
        '''clones the webpage from the specified url'''
        page = Page(self.base_url, session=self.session, base_url=self.base_url)
        if self.single_page:
            return self.download_page(page=page, session=self.session, images=self.images_only, media=self.include_media)

        self.browse(self.base_url)

        if self.images_only:
            self.download(assets=self.images, session=self.session)
        else:
            self.download(assets=self.assets, pages=self.pages.values(), session=self.session)

        return

    def download_page(self, page: Page, session=None, images=False, media=True, *args, **kwargs):
        '''downloads the asset pointed to by the link'''
        images = page.get_images()
        if images:
            return self.download(images)
        cssjs = page.get_cssjs()
        if media:
            media_files = page.get_images()
        assets = [*images, *cssjs, *media_files]
        pages = [page,]
        self.download(assets=assets, pages=pages)

        
    def download(self, assets: List[Link]=[], pages: List[Page]=[], session=None, recursive=False):
        for page in pages:
            page.download()

        print("\n"*3, "*" * 8, "     DOWNLOADING STATIC FILES     ", "*" * 8, "\n")
        extra_links = set()
        for asset in assets:
            if str(asset) in self.visited_links:
                continue

            try:
                url = str(asset)
                response = session.get(url, allow_redirects=True, timeout=10)
                file = response.content

                if recursive and (asset.is_css or asset.is_js):
                    internal_links = find_urls(str(file))
                    extra_links.update(internal_links)
                save_file(path=asset.relative, content=file)
            except FileAlreadyExists:
                continue
            except Exception:
                logger.exception('file download failed')
                print("--", asset)
                STATS['errors'] += 1
                continue
            else:
                self.visited_links.append(url)
                print("++", asset)
                
                STATS['assets'] += 1
        if recursive:
            self.download(assets=extra_links, session=session, recursive=False)
    

    def browse(self, homepage: str):
        '''downloads all the static pages
        then adds all the static files to ``static_assets``,
        queue all the unprocessed site links for further
        processing
        '''
        homepage = Link(homepage, page_url=homepage, base_url=self.base_url)
        self.site_links.append(homepage)
        print('Browsing site...')
        while len(self.site_links) and len(self.pages) < MAX_PAGES:
            link = self.site_links.pop()
            
            if not validate_url(str(link), check_if_exist=False):
                logger.error(f'Badly formed URL: {str(link)}')
                continue
            if str(link) in self.pages.keys():
                continue

            print('++ {}'.format(str(link)))
            try:
                page = Page(link, session=self.session, base_url=self.base_url)
                self.pages[str(link)] = page
                self.images.update(page.get_images())
                self.cssjs.update(page.get_cssjs())
                self.media.update(page.get_media())
                self.site_links.extend(page.get_links())

            except:
                STATS['errors'] += 1
                logger.exception(f'-- failed {str(link)}')
            else:
                STATS['pages'] += 1
