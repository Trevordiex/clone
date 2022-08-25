from email.mime import base
import os
import sys
import logging
from bs4 import BeautifulSoup
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

class Page:

    def __init__(self, url, base_url=None):
        self.url = url
        self.session = requests.session()
        self.asset_urls = []
        self.base_url = base_url or url

    def download(self, link):
        response = self.session.get(link, allow_redirects=True)

        f = BytesIO(response.content)
        return f
        
    def process(self):
        index = self.download(self.url)
        soup = BeautifulSoup(index, 'html.parser')
        links = soup.find_all('link')
        imgs = soup.find_all('img')
        scripts = soup.find_all('script')
        self.asset_urls.extend([l['href'] for l in links])
        self.asset_urls.extend([i['src'] for i in imgs])
        self.asset_urls.extend([s['src'] for s in scripts if s.has_attr('src')])

        with open('index.html', 'wb') as f:
            f.write(index.getbuffer())
       


    def create_files(self):
        name = 'static'
        cwd = os.getcwd()
        folder = os.path.join(cwd, name)
        if not os.path.exists(folder):
            os.mkdir(folder)

        for file_url in self.asset_urls:
            try:
                print(file_url)
                filename = folder + '/' + file_url
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                if not file_url.startswith('http'):
                    url = self.base_url + file_url
                else:
                    url = self.base_url
                with open(filename, 'wb') as f:
                    res = self.download(url)
                    f.write(res.getbuffer())
            except:
                logger.exception('something went wrong: ')


if __name__ == '__main__':
    url = sys.argv[1]
    p = Page(url)
    p.process()
    p.create_files()