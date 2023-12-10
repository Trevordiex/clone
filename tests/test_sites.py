from unittest import TestCase, mock
import requests
from requests import Response
import io

from sites import Site, Page
from exceptions import PageNotFoundError, AuthenticationError

PAGE_LINK = 'https://example.com/about'
PAGE404 = 'https://example.com/404'
PAGE403 = 'https://example.com/403'

with open('tests/test_files/input.html') as f:
    PAGE_CONTENT = f.read()


def mock_get(*args, **kwargs):
    res = Response()
    if args[1] == PAGE_LINK:
        res.status_code = 200
        res._content = PAGE_CONTENT
    elif args[1] == PAGE404:
        res.status_code = 404
    elif args[1] == PAGE403:
        res.status_code = 403
    return res

def mock_request(*args, **kwargs):
    return mock_get


class PageTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = requests.Session()

    @mock.patch('requests.Session.get', new_callable=mock_request)
    def setUp(self, mocked_function) -> None:
        self.page = Page(PAGE_LINK, self.session, base_url='https://example.com')

    @mock.patch('requests.Session.get', new_callable=mock_request)
    def test_page_init(self, mocked_function):
        page = Page(PAGE_LINK, self.session, base_url='https://example.com')
        self.assertIsInstance(page, Page)

    @mock.patch('requests.Session.get', new_callable=mock_request)
    def test_required_parameters(self, mocked_function):
        with self.assertRaises(TypeError):
            Page(PAGE_LINK, self.session, 'https://example.com')
        with self.assertRaises(TypeError):
            Page(PAGE_LINK, self.session)

    @mock.patch('requests.Session.get', new_callable=mock_request)
    def test_attributes_are_correct(self, mocked_function):
        page = Page(PAGE_LINK, self.session, base_url='https://example.com')
        self.assertEqual(page.url, PAGE_LINK)
        self.assertEqual(page.base_url, 'https://example.com')
        self.assertIsNotNone(page.content)

    @mock.patch('requests.Session.get', new_callable=mock_request)
    def test_get_works(self, mocked_request):
        page = self.page
        self.assertEqual(page.content, PAGE_CONTENT)
        
        with self.assertRaises(PageNotFoundError):
            Page.get(PAGE404, self.session)

        with self.assertRaises(AuthenticationError):
            Page.get(PAGE403, self.session)
        
    def test_get_images_works(self):
        images = self.page.get_images()
        self.assertIsInstance(images, list)
        self.assertEqual(len(images), 3)

    def test_get_cssjs_works(self):
        cssjs = self.page.get_cssjs()
        self.assertIsInstance(cssjs, list)
        self.assertEqual(len(cssjs), 6)

    def test_get_links_works(self):
        links = self.page.get_links()
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 5)



class SiteTestCase(TestCase):
    
    def setUp(self) -> None:
        self.site = Site('https://example.com', user='trevor', password='password')
    
    def test_init_works(self):
        site = Site('https://example.com')
        self.assertIsInstance(site, Site)

    def test_has_right_attribute(self):
        site = self.site
        self.assertEqual(site.session.auth, ('trevor', 'password'))
        self.assertEqual(site.base_url, 'https://example.com')
        self.assertIsInstance(site.session, requests.Session)
        self.assertEqual(site.sitename, 'example')

        self.assertEqual(site.pages, {})
        self.assertEqual(len(site.visited_paths), 0)
        self.assertEqual(len(site.site_links), 0)
        self.assertIsInstance(site.images, set)
        self.assertIsInstance(site.cssjs, set)
        self.assertIsInstance(site.media, set)
        self.assertEqual(len(site.assets), 0)

    @mock.patch('sys.stdout', new_callable=io.StringIO)
    @mock.patch('requests.Session.get', new_callable=mock_request)
    def test_browse_works(self, mocked_request, mocked_io):
        site = self.site
        self.assertEqual(len(site.assets), 0)
        site.browse(PAGE_LINK)
        self.assertEqual(len(site.cssjs), 6)
        self.assertEqual(len(site.assets), 9)

