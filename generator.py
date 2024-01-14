'''module for generating all the css files linked to a html page'''

import re
from bs4 import BeautifulSoup as bs4
from io import BytesIO, TextIOWrapper
from typing import Union, List

from exceptions import InvalidInputError
from models import Link, url_pattern

class Parser:
    '''A class which generates static files and links from a html page

    ...

    Attributes
    ----------
    page (html)
        the html page parsed by ``BeautifulSoup``
    complete_document (bool)
        True if page is html root tag
    base_url (str)
        the base url of the page site
    
    
    Methods
    --------
    download
        Downloads the assets in the transform
    get_links
        returns a set of links of the assets
    search
        search for an asset in a page

    Note:
        The list returned by each method contains the absolute urls of the file or
        the full link path as the case may be and not the actual file object
    '''

    def __init__(
            self,
            *,
            html: Union[str, bytes],
            page_url: str,
            base_url: str
        ) -> None:
        if isinstance(html, (str, bytes, BytesIO, TextIOWrapper)):
            self.page = bs4(html, 'html.parser')
        elif isinstance(html, bs4):
            self.page = html
        else:
            raise InvalidInputError()
        self.base_url = base_url
        self.page_url = page_url
        self.transforms = {}

    def url_to_links(self, urls: List[str]) -> List[Link]:
        return Link.url_to_links(
            urls=urls,
            page_url=self.page_url,
            base_url=self.base_url
        )
    
    
    def get_links(self):
        '''generates a list of all the internal links in the page'''

        links = self.page.find_all('a')
        links = [link['href'] for link in links if link.get('href', None)]

        return self.url_to_links(links)
    
    def get_cssjs(self) -> List[Link]:
        '''generates the page css and js files
        ----
        For convenience, this will include all the images and all other static assets
        linked inside `style` tag
        '''
        links = self.page.find_all('link')
        stylesheets = [ link['href'] for link in links if link.get('href', None)]
        styles = self.page.find_all('style')
        for style in styles:
            links = [match[1] for match in re.findall(url_pattern, style.prettify())]
            stylesheets.extend(links)


        scripts = self.page.find_all('script')
        scripts = [js['src'] for js in scripts if js.get('src', None)]
        javascripts = self.page.find_all('script')
        for javascript in javascripts:
            links = [match[1] for match in re.findall(url_pattern, javascript.prettify())]
            scripts.extend(links)

        return self.url_to_links(urls=[*stylesheets, *scripts])
    
    def get_images(self) -> List[Link]:
        '''generates all the images in a html page'''

        images = self.page.find_all('img')
        images = [image['src'] for image in images if image.get('src', None)]
        ims = [img['href'] for img in self.page.find_all('link') if 'icon' in img.get('rel', [])]
        assets = images + ims
        
        return self.url_to_links(assets)
    
    def get_media(self) -> List[Link]:
        '''generates all media assets link fonts and videos'''
        return []