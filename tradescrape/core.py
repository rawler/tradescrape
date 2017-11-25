from asyncio import gather, sleep, CancelledError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import environ
from smtplib import SMTP
from urllib.parse import urlparse, urlunparse, ParseResult
from traceback import print_exc

from tradescrape import scrapers, ArgumentFailure


def send_email(recipient, subject, body, *, type='plain'):
    gmail_user = environ['GMAIL_USER']
    gmail_pwd = environ['GMAIL_PASSWORD']

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = gmail_user
    msg['To'] = recipient
    msg.attach(MIMEText(body, type))

    try:
        server = SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.close()
        print('successfully sent the mail')
    except Exception as e:
        print("failed to send mail", e)


def dispatch(url):
    try:
        return scrapers[urlparse(url).hostname]
    except KeyError:
        raise ArgumentFailure('Unknown scraper for', url)


async def scrape_from(url, param):
    async for href, label, img in dispatch(url)(url, param):
        if not isinstance(href, ParseResult):
            href = urlparse(href)
        if img and not isinstance(img, ParseResult):
            img = urlparse(img)

        for url in (href, img):
            if url and (url.scheme == '' or url.netloc == ''):
                raise Exception("Global URL required", url)

        yield urlunparse(href), label, (urlunparse(img) if img else None)


class ScrapeRun:
    def __init__(self, db, dry):
        self.db = db
        self.dry = dry

    async def _scrape_source(self, url, param):
        async for href, label, img in scrape_from(url, param):
            new, item = self.db.upsert_item(href, label=label, imgurl=img)
            if new:
                self.emit(item)

    def emit(self, item):
        if self.dry:
            return
        body = '''<a href="%s">%s</a><br><img src="%s">''' % (item.href, item.href, item.imgurl)
        send_email(environ['NOTIFY_MAIL'], item.label, body, type='html')

    async def __call__(self):
        executor = gather(*(self._scrape_source(x.url, x.param) for x in self.db.list_sources()))
        if self.dry:
            await executor
        else:
            with self.db:
                await executor

    async def loop(self, interval, loop=None):
        while True:
            try:
                print("Going")
                await self()
            except CancelledError:
                raise
            except Exception:
                print_exc()
            if interval > 0:
                await sleep(interval)
            else:
                return
