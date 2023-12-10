'''Testcase for ``generator`` module

This testcase tests that the page parser generates correct
+ asset links from a html page
'''

import os
import io
from unittest import TestCase
from unittest.mock import patch

from generator import Parser

class ParserTestCase(TestCase):
    '''TestCase for Parser'''

    @classmethod
    def setUpClass(cls) -> None:
        with open('tests/test_files/input.html', 'r') as f:
            cls.page = f.read()
        cls.base_url = 'https://example.com'
    
    def setUp(self) -> None:
        self.parser = Parser(html=self.page, page_url='https://example.com/accounts/register', base_url='https://example.com')

    def test_init_works_with_correct_params(self):
        self.assertIsInstance(self.parser, Parser)
        self.assertEqual(self.parser.base_url, 'https://example.com')
        self.assertEqual(self.parser.page_url, 'https://example.com/accounts/register')

    def test_all_params_are_required(self):
        pass

    def test_url_to_link_works(self):
        urls = [
            'https://example.com/about',
            '/contact-us',
            '../account/signup',
            'https://2.example.com/static/styes/main.css'
        ]
        links = self.parser.url_to_links(urls)
        self.assertIsInstance(links, list)
        self.assertEqual(len(links), 3)
        self.assertIn('https://example.com/about', [str(s) for s in links])
        self.assertNotIn('https://2.example.com/static/styes/main.css', [str(s) for s in links])

    def test_get_links_works(self):
        links = self.parser.get_links()
        self.assertIsInstance(links, list)
        links = [str(l) for l in links]
        self.assertIn('https://example.com/accounts/register/page1.html', links)
        self.assertIn('https://example.com/accounts/register/page2.html', links)
        self.assertIn('https://example.com/accounts/register/page3.html', links)
        self.assertIn('https://example.com/accounts/register/login.html', links)
        self.assertIn('https://example.com/accounts/register/signup', links)

    def test_get_cssjs_works(self):
        cssjs = self.parser.get_cssjs()
        self.assertIsInstance(cssjs, list)
        self.assertGreater(len(cssjs), 0)
        self.assertTrue(all(str(s).startswith(self.base_url) for s in cssjs))
        self.assertIn('https://example.com/static/home/style.css', [str(s) for s in cssjs])
        self.assertTrue(all(str(s).startswith(self.base_url) for s in cssjs))
        self.assertNotIn('https://2.example.com/static/styes/main.css', [str(s) for s in cssjs])

    def test_get_images_works(self):
        images = self.parser.get_images()
        self.assertIsInstance(images, list)
        self.assertTrue(all(str(s).startswith(self.base_url) for s in images))
        self.assertIn('https://example.com/static/images/page2.jpeg', [str(s) for s in images])
