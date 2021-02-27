import websocket, json
from binance.client import Client
from binance.enums import KLINE_INTERVAL_1MINUTE
from datetime import datetime
import keys

def on_open(ws):
    print("Opened connection")

def on_close(ws):
    print("Closed connection")

def print_current_candle(candle):
    time = datetime.utcfromtimestamp(candle['t']/1000).strftime('%Y-%m-%d %H:%M:%S')
    print("Time: {} Open: {} High: {} Low: {} Close: {} Volume: {}".format(time,candle['o'],candle['h'],candle['l'],candle['c'],candle['v']))

def on_the_opening_candle():
    try:
        last_two_candles = client.get_klines(symbol='BNBUSDT', interval=Client.KLINE_INTERVAL_1MINUTE, limit=2)
        range_prev_day = float(last_two_candles[-2][2])-float(last_two_candles[-2][3])
        entry_price = float(last_two_candles[-1][1])+range_prev_day
        free_usdt = float(client.get_asset_balance(asset='USDT')['free'])
        free_bnb = float(client.get_asset_balance(asset='BNB')['free'])
        quantity = "{:0.0{}f}".format(free_usdt/entry_price, 4)
        print("Free USDT is {}, free BNB is {}".format(free_usdt,free_bnb))
        print("Entry price is {}, quantity is {}".format(entry_price,quantity))

        return entry_price, quantity
    except Exception as e:
        print("On the opening candle error: {}".format(e))

def buy(entry_price, quantity):
    try:
        print("Good price to buy")
        # client.order_limit_buy(
        #     symbol='BNBUSDT',
        #     quantity=quantity,
        #     price=entry_price
        # )
        return True
    except Exception as e:
        print("Buy order error: {}".format(e))
        return False

def on_message(ws, msg):
    try:
        json_message = json.loads(msg)
        candle = json_message['k']
        is_candle_closed = candle['x']
        if variables['is_candle_opened']:
            variables['entry_price'], variables['quantity'] = on_the_opening_candle()
            variables['is_candle_opened'] = False

        # check entry price
        if not variables['in_position'] and float(candle['h']) >= variables['entry_price']:
            variables['in_position'] = buy(variables['entry_price'], variables['quantity'])

        if is_candle_closed:
            variables['is_candle_opened'] = True

        print_current_candle(candle)
    except Exception as e:
        print("Websocket stream error: {}".format(e))

client = Client(keys.TEST_BINANCE_API, keys.TEST_BINANCE_SECRET)
client.API_URL = 'https://testnet.binance.vision/api'

# socket = "wss://testnet.binance.vision/ws/bnbusdt@kline_1m"
socket = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"

variables = {
    'is_candle_opened': True,
    'in_position': False,
    'entry_price': 9999999.,
    'quantity': 0
}

ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()