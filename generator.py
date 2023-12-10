'''module for generating all the css files linked to a html page'''

from bs4 import BeautifulSoup as bs4
from io import BytesIO, TextIOWrapper
from typing import Union, List

from exceptions import InvalidInputError
from models import Link

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
        links = []
        for link in set(urls):
            if Link.is_internal(link, self.base_url):
                links.append(Link(
                    link=link,
                    page_url=self.page_url,
                    base_url=self.base_url
                ))
        return links
    
    
    def get_links(self):
        '''generates a list of all the internal links in the page'''

        links = self.page.find_all('a')
        links = [link['href'] for link in links if link.get('href', None)]

        return self.url_to_links(links)
    
    def get_cssjs(self) -> List[Link]:

        links = self.page.find_all('link')
        stylesheets = [ link['href'] for link in links if 'stylesheet' in link.get('rel', [])]

        scripts = self.page.find_all('script')
        scripts = [js['src'] for js in scripts if js.get('src', None)]

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