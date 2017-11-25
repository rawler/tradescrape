from tradescrape.scraper import SimpleHTTPScraper


class Blocket(SimpleHTTPScraper):
    def query_url(self, q):
        return 'https://www.blocket.se/hela_sverige?q=%s&cg=2040&w=3&st=s&c=2045&ca=11&is=1&l=0&md=th' % self.esc(q)

    def items(self, page):
        return page.find(id="item_list").find_all('article', class_="item_row")

    def href(self, item):
        return item.find('a', class_="item-link")

    def label(self, item):
        return item.find('h1', class_='media-heading')

    def img(self, item):
        tag = item.find('a', class_="image_container").find('img')
        try:
            return tag['longdesc']
        except (KeyError, TypeError):
            return tag
