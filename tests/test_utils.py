import os
from io import BytesIO
from unittest import TestCase

from utils import make_byte, make_relative, validate_url, save_file, is_file_path

class UtilsTestCase(TestCase):
    def test_make_byte_works(self):
        self.assertIsInstance(make_byte('string'), bytes)

    def test_make_relative(self):
        transforms = {
            b'contact.html': b'https://example.com/about',
            b'?register': b'https://example.com/?register'
        }
        page = b'<a href="contact.html">this is just a basic html to test things</a>. as you may well know, this is another <a href="?register">link</a>'
        transformed = make_relative(page, transforms)
        for val in transforms.values():
            self.assertIn(val, transformed)

    def test_validate_url(self):
        good = [
            'http://localhost',
            'https://example.com',
            'http://example.com:80',
            'https://www.example.com'
        ]

        bad = [
            'htt://localhost',
            'http://example com'
        ]

        for url in good:
            self.assertTrue(validate_url(url))
        for url in bad:
            self.assertFalse(validate_url(url))

    def test_save_file(self):
        if os.path.exists('test'):
            os.remove('test')

        save_file('test', b'')
        self.assertIn('test', os.listdir())
        os.remove('test')

    def test_is_file_path(self):
        self.assertTrue(is_file_path('http://localhost/example.html'))
        self.assertFalse(is_file_path('http://localhost/example'))