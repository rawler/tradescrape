from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib.parse import urljoin as uj, quote


class SimpleHTTPScraper:
    '''Needs concrete implementation

    def query_url(self, q): ...
    def items_container(self, page): ...
    def href(self, item): return "url"
    def label(self, item): return "label"
    def img(self, item): return "img_url" or None

    Optionally:
    def post(self, param): return dict(post_body)
    '''

    @staticmethod
    def esc(q):
        return quote(q)

    async def __call__(self, url, param):
        with ClientSession() as session:
            if hasattr(self, 'post'):
                req = session.post(url, data=self.post(url, param))
            else:
                req = session.get(url)

            async with req as resp:
                soup = BeautifulSoup(await resp.read(), 'html.parser')
                for item in self.items(soup):
                    href = self.href(item)
                    if isinstance(href, Tag):
                        href = href['href']

                    label = self.label(item)
                    if isinstance(label, Tag):
                        label = label.text

                    img = self.img(item)
                    if isinstance(img, Tag):
                        img = img['src']

                    yield uj(url, href), label.strip(), (uj(url, img) if img else None)
