from tradescrape import blocket, bortskankes, pn_trading

scrapers = {
    'www.bortskankes.se': bortskankes.Bortskankes(),
    'www.pn-trading.se': pn_trading.PnTrading(),
    'www.blocket.se': blocket.Blocket(),
}


class ArgumentFailure(Exception):
    pass
