from sqlite3 import connect
from os import path

locations = [
    "tradescrape.db",
    "~/.tradescrape.db",
]


def _join(values, delim=", "):
    def _str(v):
        if isinstance(v, tuple):
            return "%s=%s" % v
        else:
            return str(v)
    return delim.join(map(_str, values))


class DB:
    def __init__(self, path):
        self.db = connect(path)
        self.db.executescript("""
CREATE TABLE IF NOT EXISTS source (id INTEGER PRIMARY KEY, url TEXT NOT NULL, param TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS source_unique ON source (url, param);

CREATE TABLE IF NOT EXISTS items (href TEXT PRIMARY KEY, label TEXT NOT NULL, imgurl TEXT);
""")

    def __enter__(self):
        return self.db.__enter__()

    def __exit__(self, type, value, tb):
        return self.db.__exit__(type, value, tb)

    def _get_single_row(self, q, *args):
        c = self.db.cursor()
        c.execute(q, args)
        return c.fetchone()

    def _get_single_value(self, q, *args):
        return self._get_single_row(q, *args)[0]

    def _get_objects(self, t, q, *args):
        c = self.db.cursor()
        c.execute(q, args)
        header = list((idx, col[0]) for idx, col in enumerate(c.description))
        for row in c:
            yield t(self, **{col: row[idx] for idx, col in header})

    def _get_object(self, t, q, *args):
        x = self._get_objects(t, q, *args)
        v = next(x)
        try:
            next(x)
        except StopIteration:
            return v
        else:
            raise Exception("Non-unique query")

    def _insert(self, table, **values):
        keys, values = zip(*values.items())
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (table, _join(keys), _join('?' * len(values)))
        self.db.execute(sql, values)

    def _upsert(self, table, crit, **values):
        crit_keys = _join((v, '?') for v in crit.keys())
        value_keys = _join((v, '?') for v in values.keys())
        sql = "UPDATE %s SET %s WHERE %s" % (table, value_keys, crit_keys)
        c = self.db.cursor()
        c.execute(sql, list(values.values()) + list(crit.values()))
        if c.rowcount == 0:
            self._insert(table, **crit, **values)
            return True
        else:
            return False

    def add_source(self, url, param):
        with self.db:
            self._insert("source", url=url, param=param)

        s = self.get_source(url, param)
        return s

    def get_source(self, url, param):
        if param is None:
            return self._get_object(Source, "SELECT * FROM source WHERE url=? AND param IS NULL", url)
        else:
            return self._get_object(Source, "SELECT * FROM source WHERE url=? AND param=?", url, param)


    def list_sources(self):
        return self._get_objects(Source, "SELECT * FROM source")

    def rm_source(self, url, param=None):
        with self.db:
            if param is None:
                self.db.execute("DELETE FROM source WHERE url=?", (url,))
            else:
                self.db.execute("DELETE FROM source WHERE url=? AND param=?", (url, param))

    def upsert_item(self, href, **values):
        new = self._upsert("items", {"href": href}, **values)
        return new, self._get_object(Item, "SELECT * FROM items WHERE href=?", href)


class RowItem:
    def __init__(self, db, **values):
        self._db = db
        for k, v in values.items():
            setattr(self, k, v)

    def __repr__(self):
        return "<%s %s>" % (type(self).__name__, _join((k, getattr(self, k)) for k in self.keys))

    @property
    def keys(self):
        return (x for x in self.__dict__.keys() if not x.startswith('_'))


class Source(RowItem):
    pass


class Item(RowItem):
    pass


def open(search=locations):
    for p in search:
        if path.exists(p):
            return DB(p)
    return DB(search[0])
