'''utility functions for url transforms'''

import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from enum import Enum

from url_parser import parse_url


def resolve(base_url: str, link: str) -> str:
    '''resolves a relative url into an absolute url'''
    link = link or ''
    if link == '/':
        rpath = ''
    else:
        rpath = link.lstrip('/')

    fpath = os.path.join(base_url, rpath)
    return os.path.normpath(fpath).replace(':/', '://')


def remove_fragment(link: str) -> str:
    '''removes the fragment part of the url'''
    parts = urlparse(link)
    return urlunparse(parts._replace(fragment=''))

def remove_query(link: str) -> str:
    parts = urlparse(link)
    return urlunparse(parts._replace(query=''))

def is_file_path(link: str) -> bool:
    '''returns True if a link is an actual file path
    
    i.e link string ends with a page suffix (https://.../login.php)
    '''
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?P<path>[/?]\S+)$', re.IGNORECASE)
    
    match = re.match(regex, link)
    if match:
        path = match.group('path')
        return True if Path(path).suffix else False
    return False
    

    

def ping(url: str) -> bool:
    '''checks if the url is online and active'''
    r = requests.head(url)
    return r.status_code == 200


def validate_url(url, check_if_exist: bool = False):
    '''checks for the validity of a url string.
    ...
    Note
    ----
    regex copied from django URLValidator
    '''

    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    valid =  re.match(regex, url) is not None
    if check_if_exist:
        return valid and ping(url)
    return valid


class Link:
    '''A model of HTML link
    used to resolve and convert to absolute url
    ...

    Attributes
    ---------

    '''

    PAGE_SUFFIXES = ['.html', '.php', '.aspx', '.css', '.js', '.png', '.svg', '.jpg', '.jpeg']

    class LinkType(Enum):
        ABSOLUTE = 1
        RELATIVE = 2
        QUERY = 3

    def __init__(self, link: str, *, link_type: LinkType = None, page_url: str = None, base_url: str=None ) -> None:
        self.link = link
        self.type = link_type
        self.page_url = page_url
        self.base_url = base_url or self.page_url

    def __str__(self):
        return self.normalize()
    
    def __repr__(self) -> str:
        return f'<Link: {str(self)}>'

    def normalize(self) -> str:
        link = self.link
        if self.type == self.LinkType.RELATIVE:
            if is_file_path(self.page_url):
                if self.link.startswith('./'):
                    link = link.replace('./', '../', 1)
                elif self.link[0].isalpha() or self.link.startswith('../'):
                    link = '../' + link
            base_url = self.page_url
        elif self.type == self.LinkType.ABSOLUTE:
            base_url = self.base_url
        elif self.type == self.LinkType.QUERY:
            base_url = self.page_url
        
        return resolve(base_url, link)
    

    def url_to_path(self) -> str:
        '''converts a site page link to a file system path'''
        # for links that use query params e.g ?a=about.html
        if self.type == self.LinkType.QUERY:
            parsed_url = parse_url(str(self))
            query = parsed_url['query']
            name = list(query.values())[0]
            if not Path(name).suffix in self.PAGE_SUFFIXES:
                name = name + '.html'
            path = os.path.join(parsed_url['path'], name)
            
        else:
            parsed_url = parse_url(str(self))
            path = parsed_url['path']
            if path is None or path == '/':
                path = 'index.html'
            path = path.strip('/')
            path = path if Path(path).suffix in self.PAGE_SUFFIXES else path + '.html'
        
        # change page file suffix to html
        suffix = Path(path).suffix
        if suffix in ['.php', '.aspx']:
            path = path.replace(suffix, '.html')
        return path.lstrip('/')
    
    @property
    def relative(self) -> str:
        return self.url_to_path()
    
    def __eq__(self, __o: object) -> bool:
        return str(self) == str(__o)
    
    def __ne__(self, __o: object) -> bool:
        return not str(self) == str(__o)
    
    def __hash__(self) -> int:
        return super().__hash__()