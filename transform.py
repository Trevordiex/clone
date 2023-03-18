'''string/bytes transforms to make html pages use only relative urls'''

def make_byte(s: str) -> bytes:
    return bytes(s, encoding='utf8')

def make_relative(page: bytes, transforms: dict) -> bytes:
    '''performs a search and replace using ``tranforms`` as a map'''
    for key, value in transforms.items():
        page = page.replace(key, value)

    return page