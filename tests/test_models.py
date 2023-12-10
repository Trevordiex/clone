from unittest import TestCase

from models import Link


class ModelTestCase(TestCase):
    def setUp(self) -> None:
        self.link = Link(
            '/accounts/signup',
            page_url='https://example.com/accounts/login',
            base_url='https://example.com'
        )

    def test_init_works(self):
        self.assertIsInstance(self.link, Link)
        with self.assertRaises(TypeError):
            Link('https://example.com/about')
        
        with self.assertRaises(TypeError):
            Link('https://example.com/about', page_url='about')
        with self.assertRaises(TypeError):
            Link('https://example.com/about', base_url='about')

    def test_query_type_is_well_represented(self):
        self.assertTrue(Link.is_query('?page=1', ''))
        self.assertFalse(Link.is_query('https://example.com', ''))
        self.assertFalse(Link.is_query('register.html', ''))

    def test_relative_type_is_well_represented(self):
        self.assertTrue(Link.is_relative('register.html', ''))
        self.assertTrue(Link.is_relative('./register.html', ''))
        self.assertFalse(Link.is_relative('https://example.com', ''))
        self.assertFalse(Link.is_relative('?page=1', 'https://example.com'))

    def test_absolute_type_is_well_represented(self):
        self.assertTrue(Link.is_absolute('https://example.com/about', 'https://example.com'))
        self.assertTrue(Link.is_absolute('/about', ''))
        self.assertFalse(Link.is_absolute('about.html', 'https://example.com'))
        self.assertFalse(Link.is_absolute('?page=1', 'https://example.com'))

    def test_internal_links_is_well_represented(self):
        ls = ['', '#', 'tel:7080', 'mailto:email', 'javascript:void()', 'data:image//ljhd', ';base64://43ds4e']
        for link in ls:
            self.assertFalse(Link.is_internal(link, ''))
        self.assertTrue(Link.is_internal('?page=1', ''))
        self.assertTrue(Link.is_internal('register.html', ''))
        self.assertTrue(Link.is_internal('/accounts/login', ''))

    def test_link_type_is_accurate(self):
        self.assertEqual(Link.get_link_type('?page=1', ''), Link.LinkType.QUERY)
        self.assertEqual(Link.get_link_type('register.html', ''), Link.LinkType.RELATIVE)
        self.assertEqual(Link.get_link_type('../relative', ''), Link.LinkType.RELATIVE)
        self.assertEqual(Link.get_link_type('/absolute', ''), Link.LinkType.ABSOLUTE)
        self.assertEqual(Link.get_link_type('https://example.com/about', 'https://example.com'), Link.LinkType.ABSOLUTE)

    def test_remove_fragment_works(self):
        self.assertEqual(Link.remove_fragment('https://example.com/#frag'), 'https://example.com/')

    def test_url_can_normalize(self):
        l1 = Link('/account/login', page_url='https://example.com/account', base_url='https://example.com')
        l2 = Link('login', page_url='https://example.com/account', base_url='https://example.com')
        l3 = Link('?login=page', page_url='https://example.com/account', base_url='https://example.com')
        l4 = Link('https://example.com/account/login', page_url='', base_url='')

        self.assertEqual(str(l1), 'https://example.com/account/login')
        self.assertEqual(str(l2), 'https://example.com/account/login')
        self.assertEqual(str(l3), 'https://example.com/account/?login=page')
        self.assertEqual(str(l4), 'https://example.com/account/login')

    def test_url_converts_to_path(self):
        l1 = Link('?page=login', page_url='https://example.com/account', base_url='https://example.com')
        l2 = Link('login', page_url='https://example.com/account', base_url='https://example.com')
        self.assertEqual(l1.url_to_path(), 'account/login.html')
        self.assertEqual(l2.url_to_path(), 'account/login.html')