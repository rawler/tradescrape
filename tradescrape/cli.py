from tradescrape import core, db, ArgumentFailure
from asyncio import get_event_loop
from functools import partial


def printf(fmt, *args, **kwargs):
    print(fmt.format(*args, **kwargs))


def printrow(args, sep='\t'):
    print(sep.join(args))


class CommandGroup:
    def __init__(self, dbpath=None):
        if dbpath:
            self.db = db.open([dbpath])
        else:
            self.db = db.open()


class Sources(CommandGroup):
    def _print(self, s):
        if s.param:
            printf("{url}: {param}", **vars(s))
        else:
            print(s.url)

    def add(self, url, param):
        core.dispatch(url)  # Throws ArgumentError on unknown
        s = self.db.add_source(url, param)
        self._print(s)

    def list(self):
        for s in self.db.list_sources():
            self._print(s)

    def rm(self, url, param):
        self.db.rm_source(url, param)


class Run(CommandGroup):
    def run(self, dry, interval):
        runner = core.ScrapeRun(self.db, dry)
        get_event_loop().run_until_complete(runner.loop(interval))


class Test(CommandGroup):
    def run(self, url, param):
        async def _():
            async for href, label, img in core.scrape_from(url, param):
                print(href)
                print("  ", label)
                print("  ", img)
                print()

        get_event_loop().run_until_complete(_())


def subcommands(p, name):
    p = p.add_subparsers(dest=name)
    p.required = True
    return p


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser(prog='tradescrape')
    parser.add_argument('--db', metavar="DBPATH", help='path to sqlite database')
    subparsers = subcommands(parser, 'handler')

    sources_parser = subparsers.add_parser('sources', help='manage sources')
    sources_parser.set_defaults(handler=Sources)
    sources_subparsers = subcommands(sources_parser, 'action')

    sources_add_parser = sources_subparsers.add_parser('add', help='add source to track')
    sources_add_parser.set_defaults(action='add')
    sources_add_parser.add_argument('url', help='query url for items')
    sources_add_parser.add_argument('param', nargs='?', help='extra params to the query module')

    sources_list_parser = sources_subparsers.add_parser('list', help='list active sources')
    sources_list_parser.set_defaults(action='list')

    sources_remove_parser = sources_subparsers.add_parser('rm', help='add source to track')
    sources_remove_parser.set_defaults(action='rm')
    sources_remove_parser.add_argument('url', help='query url for items')
    sources_remove_parser.add_argument('param', nargs='?', help='extra params to the query module')

    run_parser = subparsers.add_parser('run', help='run ')
    run_parser.set_defaults(handler=Run)
    run_parser.set_defaults(action='run')
    run_parser.add_argument('--dry', default=False, action='store_true', help="don't save or send new items")
    run_parser.add_argument('--interval', default=120, type=int, help="Seconds between scrapings. 0 for single-shot mode")

    test_parser = subparsers.add_parser('test', help='Test scraper implementation')
    test_parser.set_defaults(handler=Test)
    test_parser.set_defaults(action='run')
    test_parser.add_argument('url', help='query url for items')
    test_parser.add_argument('param', nargs='?', help='extra params to the query module')

    args = vars(parser.parse_args())
    try:
        handler = args.pop('handler')
        action = args.pop('action')
        db = args.pop('db')
    except KeyError as e:
        parser.error('Missing ' + e.args[0])

    try:
        getattr(handler(db), action)(**args)  # Magic!
    except ArgumentFailure as f:
        parser.error("Failed: %s" % ': '.join(map(str, f.args)))
