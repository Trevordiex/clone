'''module for generating all the css files linked to a html page'''

from bs4 import BeautifulSoup as bs4
from io import BytesIO
from typing import Union, List
from url_parser import parse_url

from exceptions import InvalidInputError, EmptyPageError, BaseUrlRequiredError
from urls import Link, resolve, remove_fragment, remove_query, is_file_path
from transform import make_byte

class Generator:
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
    transforms (dict)
        A mapping of all the necessary transforms that turns
        page links into relative urls
    
    
    Methods
    --------
    generate_css
        returns a list of css files contained in a page
    generate_js
        returns a list of js files contained in a page
    generate_links
        returns a list containing all the internal links in a page
    generate_images
        returns a list contining all the images in a page

    Note:
        The list returned by each method contains the absolute urls of the file or
        the full link path as the case may be and not the actual file object
    '''

    def __init__(self, html: Union[str, bytes], page_url: str, base_url: str = None, complete_document: bool = True) -> None:
        if isinstance(html, (str, bytes, BytesIO)):
            self.page = bs4(html, 'html.parser')
        elif isinstance(html, bs4):
            self.page = html
        else:
            raise InvalidInputError()
        self.base_url = remove_query(base_url)
        self.complete_document = True
        self.page_url = remove_query(page_url)
        self.transforms = {}

    def generate_css(self) -> List[Link]:
        '''generates a list of all css files in the html page'''
        if not self.page:
            raise EmptyPageError()
        if not self.base_url:
            raise BaseUrlRequiredError()
        if not self.complete_document:
            return

        links = self.page.find_all('link')
        stylesheets = [ link['href'] for link in links if 'stylesheet' in link.get('rel', [])]
        filtered_stylesheets: List[Link] = []
        for style in set(stylesheets):
            if not style.startswith('http'):
                s_style = remove_query(style)
                if s_style.startswith('/'):
                    l = Link(s_style, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                else:
                    l = Link(s_style, link_type=Link.LinkType.RELATIVE, page_url=self.page_url, base_url=self.base_url)
                filtered_stylesheets.append(l)
            elif style.startswith(self.base_url):
                path = parse_url(style)['path']
                l = Link(path, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                filtered_stylesheets.append(l)
            else:
                continue

            self.transforms.update({make_byte('"' + style + '"'): make_byte('"' + l.relative + '"')})
        return filtered_stylesheets

    def generate_js(self) -> List[Link]:
        '''generate a list of all scripts linked to the page'''
        if not self.page:
            raise EmptyPageError()
        if not self.base_url:
            raise BaseUrlRequiredError()
        
        scripts = self.page.find_all('script')
        scripts = [js['src'] for js in scripts if js.get('src', None)]
        filtered_scripts: List[Link] = []

        for script in set(scripts):
            if not script.startswith('http'):
                s_script = remove_query(script)
                if s_script.startswith('/'):
                    l = Link(s_script, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                else:
                    l = Link(s_script, link_type=Link.LinkType.RELATIVE, page_url=self.page_url, base_url=self.base_url)
                filtered_scripts.append(l)
            elif script.startswith(self.base_url):
                path = parse_url(script)['path']
                l = Link(path, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                filtered_scripts.append(l)
            else:
                continue

            self.transforms.update({make_byte('"' + script + '"'): make_byte('"' + l.relative + '"')})
        return filtered_scripts

    def generate_links(self) -> List[Link]:
        '''generates a list of all the internal links in the page'''
        if not self.page:
            raise EmptyPageError()
        if not self.base_url:
            raise BaseUrlRequiredError()

        links = self.page.find_all('a')
        links = [link['href'] for link in links if link.get('href', None)]
        internal_links: List[Link] = []
        for link in set(links):
            link = remove_fragment(link)
            if not link or link in ['/', '#']:
                continue
            elif link.startswith('tel:') or link.startswith('mailto:'):
                continue
            elif 'javascript:void' in link:
                continue
            # elif link.startswith('?') and self.base_url != self.page_url:
            #     continue
            elif link.startswith('?'):
                l = Link(link, link_type=Link.LinkType.QUERY, page_url=self.page_url)
                internal_links.append(l)
            elif not link.startswith('http'):
                s_link = remove_query(link)
                if s_link.startswith('/'):
                    l = Link(s_link, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                else:
                    l = Link(s_link, link_type=Link.LinkType.RELATIVE, page_url=self.page_url, base_url=self.base_url)
                    
                internal_links.append(l)
            elif link.startswith(self.base_url):
                path = parse_url(link)['path']
                l = Link(path, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                internal_links.append(l)
            else:
                continue

            self.transforms.update({make_byte('"' + link + '"'): make_byte('"' + l.relative + '"')})
        return internal_links

    def generate_images(self) -> List[Link]:
        '''generates all the images in a html page'''
        if not self.page:
            raise EmptyPageError()
        if not self.base_url:
            raise BaseUrlRequiredError()

        images = self.page.find_all('img')
        images = [image['src'] for image in images if image.get('src', None)]
        ims = [img['href'] for img in self.page.find_all('link') if 'icon' in img.get('rel', [])]
        assets = images + ims
        filtered_assets: List[Link] = []
        for asset in set(assets):
            if 'data:image' in asset or ';base64' in asset:
                continue
            elif not asset.startswith('http'):
                s_asset = remove_query(asset)
                if asset.startswith('/'):
                    l = Link(s_asset, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                else:
                    l = Link(s_asset, link_type=Link.LinkType.RELATIVE, page_url=self.page_url, base_url=self.base_url)
                filtered_assets.append(l)
            elif asset.startswith(self.base_url):
                path = parse_url(asset)['path']
                l = Link(path, link_type=Link.LinkType.ABSOLUTE, page_url=self.base_url)
                filtered_assets.append(l)
            else:
                continue

            self.transforms.update({make_byte('"' + asset + '"'): make_byte('"' + l.relative + '"')})
        return filtered_assets
    
    def get_transforms(self) -> dict:
        '''returns the transform dict of the page'''
        self.generate_css()
        self.generate_js()
        self.generate_links()
        self.generate_images()

        return self.transforms