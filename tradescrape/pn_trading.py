from tradescrape.scraper import SimpleHTTPScraper


class PnTrading(SimpleHTTPScraper):
    def query_url(self, _q):
        return 'http://www.pn-trading.se/'

    def post(self, url, q):
        return{"filter": q, "page": 1}

    def items(self, page):
        return page.find(id="items-wrapper").find_all(class_="isotope_item")

    def href(self, item):
        return item.find(class_='fa-link').parent

    def label(self, item):
        return item.find('h3')

    def img(self, item):
        return item.find(class_="pic_box").find('img')
