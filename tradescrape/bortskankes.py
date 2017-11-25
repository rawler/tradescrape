from tradescrape.scraper import SimpleHTTPScraper


class Bortskankes(SimpleHTTPScraper):
    def query_url(self, q):
        return 'https://www.bortskankes.se/index.php?searchtxt=%s&showclosed=n' % self.esc(q)

    def items(self, page):
        return page.find(id="ads_table_rwd").find_all('tr', class_="ads_tr1")

    def href(self, item):
        return item.find('a')

    def label(self, item):
        return item.find('h3')

    def img(self, item):
        return item.find('img')
