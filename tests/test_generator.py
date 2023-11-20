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
    
    def setUp(self) -> None:
        self.parser = Parser(html=self.page, page_url='https://example.com/accounts/register', base_url='https://example.com')

    def test_init_works_with_correct_params(self):
        self.assertIsInstance(self.parser, Parser)
        self.assertEqual(self.parser.base_url, 'https://example.com')
        self.assertEqual(self.parser.page_url, 'https://example.com/accounts/register')

    def test_all_params_are_required(self):
        pass

    def test_get_links_works(self):
        links = self.parser.get_links()
        self.assertIsInstance(links, list)
        self.assertIn('page1.html', [str(l) for l in links])