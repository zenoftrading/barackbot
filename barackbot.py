import websocket, json
from binance.client import Client
from binance.enums import KLINE_INTERVAL_1MINUTE
from datetime import datetime

BINANCE_API = ''
BINANCE_SECRET = ''

TEST_BINANCE_API = ''
TEST_BINANCE_SECRET = ''

# for testnet trading
test_client = Client(TEST_BINANCE_API, TEST_BINANCE_SECRET)
test_client.API_URL = 'https://testnet.binance.vision/api'
# test_socket = "wss://testnet.binance.vision/ws/bnbusdt@kline_1m"

# for production and real prices
client = Client(BINANCE_API, BINANCE_SECRET)
socket = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"

is_candle_opened = True
in_position = False
entry_price = 9999999.
quantity = 0.1
free_usdt = 0

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

def on_the_opening_candle():
    """Calculation purchase price when new cande is opened

    Returns:
        float: purchase price
    """
    global free_usdt, client, test_client
    try:
        last_two_candles = client.get_klines(symbol='BNBUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=2)
        range_prev_day = float(last_two_candles[-2][2])-float(last_two_candles[-2][3])
        entry_price = float(last_two_candles[-1][1])+range_prev_day
        new_free_usdt = float(test_client.get_asset_balance(asset='USDT')['free'])
        free_bnb = float(test_client.get_asset_balance(asset='BNB')['free'])
        free_usdt = new_free_usdt
        print("Free USDT is {}, free BNB is {}".format(new_free_usdt,free_bnb))
        print("Entry price is {} USDT, quantity is {} BNB".format(entry_price,quantity))

        return entry_price
    except Exception as e:
        print("On the opening candle error: {}".format(e))

def precision_price(price):
    """Format price to BNBUSDT precision. Use the get_symbol_info function to get info about a particular symbol.

    Args:
        price (float): current price

    Returns:
        float: formatted price
    """
    precision = 4
    precision_price = "{:0.0{}f}".format(price, precision)

    return precision_price

def buy(entry_price, quantity):
    """Sending buy limit order.

    Args:
        entry_price (float): buying price
        quantity (float): buying quantity

    Returns:
        boolean: True if buying order is finished and False if error
    """
    global test_client
    try:
        precision_entry_price = precision_price(entry_price)
        print("Buying {} BNB at {} USDT".format(quantity,precision_entry_price))
        order = test_client.order_limit_buy(
            symbol='BNBUSDT',
            quantity=quantity,
            price=precision_entry_price
        )
        print("Buy order info: {}".format(order))
        return True
    except Exception as e:
        print("Buy order error: {}".format(e))
        return False

def take(quantity, open_price):
    """Sending selling market order

    Args:
        open_price (float): open candle price
        quantity (float): selling quantity

    Returns:
        boolean: True if take order is finished and False if error
    """
    global free_usdt, test_client
    try:
        print("Take order. Open price is {} USDT".format(open_price))
        order = test_client.order_market_sell(
            symbol='BNBUSDT',
            quantity=quantity
        )
        new_free_usdt = float(test_client.get_asset_balance(asset='USDT')['free'])
        print("Profit is {} USDT".format(free_usdt-new_free_usdt))
        free_usdt = new_free_usdt
        print("Take order info: {}".format(order))
        return True
    except Exception as e:
        print("Take order error: {}".format(e))
        return False

def stop(quantity, open_price):
    """Sending selling market order

    Args:
        open_price (float): open candle price
        quantity (float): selling quantity

    Returns:
        boolean: True if stop order is finished and False if error
    """
    global free_usdt, test_client
    try:
        print("Stop order. Open price is {} USDT".format(open_price))
        order = test_client.order_market_sell(
            symbol='BNBUSDT',
            quantity=quantity
        )
        new_free_usdt = float(test_client.get_asset_balance(asset='USDT')['free'])
        print("Loss is {} USDT".format(new_free_usdt-free_usdt))
        free_usdt = new_free_usdt
        print("Stop order info: {}".format(order))
        return True
    except Exception as e:
        print("Stop order error: {}".format(e))
        return False

def on_message(ws, msg):
    """Main algo function

    Args:
        ws: websocket
        msg: websocket message
    """
    global is_candle_opened, in_position, entry_price, quantity
    try:
        json_message = json.loads(msg)
        candle = json_message['k']
        is_candle_closed = candle['x']
        if is_candle_opened:
            if in_position:
                # stop or take
                if float(candle['o']) > entry_price:
                    take(quantity, candle['o'])
                    in_position = False
                elif float(candle['o']) <= entry_price:
                    stop(quantity, candle['o'])
                    in_position = False
            entry_price = on_the_opening_candle()
            is_candle_opened = False

        # check entry price
        if not in_position and float(candle['h']) >= entry_price:
            in_position = buy(entry_price, quantity)

        if is_candle_closed:
            is_candle_opened = True

        print_current_candle(candle)
    except Exception as e:
        print("Websocket stream error: {}".format(e))

ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()