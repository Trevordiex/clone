'''utility functions for url transforms'''

import os
import re
import requests
import logging
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from enum import Enum

from url_parser import parse_url

from exceptions import FileAlreadyExists

def normalize(link: str, page_url: str, base_url: str = None) -> str:
    base_url = base_url or page_url
    if not link.startswith('http'): # link is internal
        if link.startswith('/'):
            full = link
        elif link.startswith('./'):
            full = link.replace('./', '../', 1)
            base_url = page_url
        elif link[0].isalpha() or link.startswith('../'):
            full = '../' + link
            base_url = page_url
    
        full = os.path.normpath(
            os.path.join(base_url, full.lstrip('/'))
        )
    elif link.startswith(base_url):
        full = link
        
    return full



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
    

def make_byte(s: str) -> bytes:
    return bytes(s, encoding='utf8')


def make_relative(page: bytes, transforms: dict) -> bytes:
    '''performs a search and replace using ``tranforms`` as a map'''
    for key, value in transforms.items():
        page = page.replace(key, value)

    return page


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
 
def save_file(path: str, content: BytesIO, overwrite: bool = False):
    '''creates a file path in the export directory'''
    if Path(path).exists() and not overwrite:
        logging.info(f'{path} already exists')
        raise FileAlreadyExists(f'{path} already exists')
    else:
        if '/' in path:
            dir, _ = path.rsplit('/', maxsplit=1)
            Path(dir).mkdir(parents=True, exist_ok=True,mode=0o777)

        with open(path, 'wb') as new:
            new.write(content)
        return path