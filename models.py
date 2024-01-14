'''utility functions for url transforms'''

import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from enum import Enum
from typing import List

from url_parser import get_url

from utils import is_file_path
from exceptions import InvalidInputError


url_pattern = re.compile(
    r'url\((\'|\")?'
    r'(?P<url>\S+?)' # matches the url
    r'\1?\)'
)

def find_urls(page: str) -> List[str]:
    if not isinstance(page, str):
        raise InvalidInputError('page must be a string')
    
    links = [match[1] for match in re.findall(url_pattern, page)]
    return links

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

    def __init__(self, link: str, *, page_url: str, base_url: str ) -> None:
        self.link = link
        self.page_url = page_url
        self.type = Link.get_link_type(self.link, base_url)
        self.base_url = base_url or self.page_url
        

    def __str__(self):
        return self.normalize()
    
    def __repr__(self) -> str:
        return f'<Link: {str(self)}>'

    def normalize(self) -> str:
        '''returns a link as a url (with fully qualified domain name)'''
        link = self.link
        if self.type == self.LinkType.RELATIVE:
            if is_file_path(self.page_url):
                if self.link.startswith('./'):
                    link = link.replace('./', '../', 1)
                elif self.link[0].isalpha() or self.link.startswith('../'):
                    link = '../' + link
            base_url = self.page_url
        elif self.type == self.LinkType.ABSOLUTE:
            if self.link.startswith(self.base_url):
                return self.link
            base_url = self.base_url
        elif self.type == self.LinkType.QUERY:
            base_url = self.page_url
        
        fpath = os.path.join(base_url, link.lstrip('/'))
        return os.path.normpath(fpath).replace(':/', '://')
    

    def url_to_path(self) -> str:
        '''converts a site page link to a file system path'''
        # for links that use query params e.g ?a=about.html
        if self.type == self.LinkType.QUERY:
            parsed_url = get_url(str(self))
            query = parsed_url.query
            name = list(query.values())[0]
            if not Path(name).suffix in self.PAGE_SUFFIXES:
                name = name + '.html'
            path = os.path.join(parsed_url.path, name)
            
        else:
            parsed_url = get_url(str(self))
            path = parsed_url.path
            if path is None or path == '/':
                path = 'index.html'
            path = path.strip('/')
            path = path if Path(path).suffix else path + '.html'
        
        # change page file suffix to html
        suffix = Path(path).suffix
        if suffix in ['.php', '.aspx']:
            path = path.replace(suffix, '.html')
        return path.lstrip('/')
    
    @property
    def relative(self) -> str:
        return self.url_to_path()
    
    @property
    def is_css(self):
        '''Returns `True` if filename ends with `.css`'''
        return Path(self.relative).suffix == '.css'
    
    @property
    def is_js(self):
        '''Returns `True` if filename ends with `.js`'''
        return Path(self.relative).suffix == '.js'
            
    @staticmethod
    def is_internal(link, base_url):
        '''checks if the link points to a seperate page in the same site'''
        # link = Link.remove_fragment(link)
        if any([
            not link,
            link in ['/', '#'],
            link.startswith('//'),      # protocol relative urls
            link.startswith('tel:'),
            link.startswith('mailto:'),
            'javascript:void' in link,
            'data:image' in link, # for image links
            ';base64' in link
        ]):
            return False
        
        if any([
            Link.is_absolute(link, base_url),
            Link.is_relative(link, base_url),
            Link.is_query(link, base_url)
        ]):
            return True
        return False
    
    @staticmethod
    def is_absolute(link: str, base_url: str):
        if link.startswith(base_url) or link.startswith('/'):
            return True
        return False
    
    @staticmethod
    def is_relative(link: str, base_url: str):
        if not (
            link.startswith('http')
            or link.startswith('/')
            or link.startswith('?')
        ):
            return True
        return False
    
    @staticmethod
    def is_query(link: str, base_url: str):
        if link.startswith('?'):
            return True
        return False
    
    @classmethod
    def get_link_type(cls, link: str, base_url: str):
        if cls.is_query(link, base_url):
            return cls.LinkType.QUERY
        elif cls.is_relative(link, base_url):
            return cls.LinkType.RELATIVE
        elif cls.is_absolute(link, base_url):
            return cls.LinkType.ABSOLUTE
        
    def remove_fragment(link: str) -> str:
        '''removes the fragment part of the url'''
        parts = urlparse(link)
        return urlunparse(parts._replace(fragment=''))
    
    @classmethod
    def url_to_links(cls, urls: List[str], page_url: str, base_url: str) -> List:
        links = []
        for link in set(urls):
            link = '#'.join(link.split('#')[:2])

            if cls.is_internal(link, base_url):
                links.append(cls(
                    link=link,
                    page_url=page_url,
                    base_url=base_url
                ))
        return links
    
    def __eq__(self, __o: object) -> bool:
        return str(self) == str(__o)
    
    def __ne__(self, __o: object) -> bool:
        return not str(self) == str(__o)
    
    def __hash__(self) -> int:
        return super().__hash__()
    