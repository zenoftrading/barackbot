from binance.client import Client
from binance.enums import *
from datetime import datetime
import settings

def on_open(ws):
    """Do something when websocket opening.

    Args:
        ws: current websocket
    """
    print("Opened connection")

def on_close(ws):
    """Do something when websocket closing.

    Args:
        ws: current websocket
    """

    print("Closed connection")

def print_current_candle(candle):
    """Printing current candle. Read more https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#klinecandlestick-streams

    Args:
        candle (list): candle info
    """
    time = datetime.utcfromtimestamp(candle['t']/1000).strftime('%Y-%m-%d %H:%M:%S')
    print("Time: {} Open: {} High: {} Low: {} Close: {} Volume: {}".format(time,candle['o'],candle['h'],candle['l'],candle['c'],candle['v']))

def on_the_opening_candle(client,test_client,quantity,free_usdt):
    """Calculation purchase price when new cande is opened

    Returns:
        float: purchase price
    """
    # global free_usdt, client, test_client, BASE, QUOTE, SYMBOL
    try:
        last_two_candles = client.get_klines(symbol=settings.SYMBOL, interval=Client.KLINE_INTERVAL_1MINUTE, limit=2)
        range_prev_day = float(last_two_candles[-2][2])-float(last_two_candles[-2][3])
        entry_price = float(last_two_candles[-1][1])+range_prev_day
        new_free_usdt = float(test_client.get_asset_balance(asset=settings.QUOTE)['free'])
        free_bnb = float(test_client.get_asset_balance(asset=settings.BASE)['free'])
        free_usdt = new_free_usdt
        print("Free {} is {}, free {} is {}".format(settings.QUOTE,new_free_usdt,settings.BASE,free_bnb))
        print("Entry price is {} {}, quantity is {} {}".format(entry_price,settings.QUOTE,quantity,settings.BASE))

        return entry_price
    except Exception as e:
        print("On the opening candle error: {}".format(e))

def precision_price(price):
    """Format price to SYMBOL precision. Use the get_symbol_info function to get info about a particular symbol.

    Args:
        price (float): current price

    Returns:
        float: formatted price
    """
    precision = 4
    precision_price = "{:0.0{}f}".format(price, precision)

    return precision_price

def buy(client,entry_price,quantity):
    """Sending buy limit order.

    Args:
        entry_price (float): buying price
        quantity (float): buying quantity

    Returns:
        boolean: True if buying order is finished and False if error
    """
    # global test_client, BASE, QUOTE, SYMBOL
    try:
        precision_entry_price = precision_price(entry_price)
        print("Buying {} {} at {} {}".format(quantity,settings.BASE,precision_entry_price,settings.QUOTE))
        order = client.order_limit_buy(
            symbol=settings.SYMBOL,
            quantity=quantity,
            price=precision_entry_price
        )
        print("Buy order info: {}".format(order))
        return True
    except Exception as e:
        print("Buy order error: {}".format(e))
        return False

def take(client,quantity,open_price,free_usdt):
    """Sending selling market order

    Args:
        open_price (float): open candle price
        quantity (float): selling quantity

    Returns:
        boolean: True if take order is finished and False if error
    """
    # global free_usdt, test_client, BASE, QUOTE, SYMBOL
    try:
        print("Take order. Open price is {} {}".format(open_price,settings.QUOTE))
        order = client.order_market_sell(
            symbol=settings.SYMBOL,
            quantity=quantity
        )
        new_free_usdt = float(client.get_asset_balance(asset=settings.QUOTE)['free'])
        print("Profit is {} {}".format(free_usdt-new_free_usdt,settings.QUOTE))
        free_usdt = new_free_usdt
        print("Take order info: {}".format(order))
        return free_usdt
    except Exception as e:
        print("Take order error: {}".format(e))
        return False

def stop(client,quantity,open_price,free_usdt):
    """Sending selling market order

    Args:
        open_price (float): open candle price
        quantity (float): selling quantity

    Returns:
        boolean: True if stop order is finished and False if error
    """
    # global free_usdt, test_client, BASE, QUOTE, SYMBOL
    try:
        print("Stop order. Open price is {} {}".format(open_price,settings.QUOTE))
        order = client.order_market_sell(
            symbol=settings.SYMBOL,
            quantity=quantity
        )
        new_free_usdt = float(client.get_asset_balance(asset=settings.QUOTE)['free'])
        print("Loss is {} {}".format(new_free_usdt-free_usdt,settings.QUOTE))
        free_usdt = new_free_usdt
        print("Stop order info: {}".format(order))
        return free_usdt
    except Exception as e:
        print("Stop order error: {}".format(e))
        return False