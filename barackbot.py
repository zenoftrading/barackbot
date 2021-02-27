import websocket, json
from binance.client import Client
from datetime import datetime
import keys

def on_open(ws):
    print("Opened connection")

def on_close(ws):
    print("Closed connection")

def on_message(ws, msg):
    try:
        json_message = json.loads(msg)
        candle = json_message['k']
        # is_candle_closed = candle['x']
        time = datetime.utcfromtimestamp(candle['t']/1000).strftime('%Y-%m-%d %H:%M:%S')
        print("Time: {} Open: {} High: {} Low: {} Close: {} Volume: {}".format(time,candle['o'],candle['h'],candle['l'],candle['c'],candle['v']))
    except Exception as e:
        print("Websocket stream error: {}".format(e))

client = Client(keys.TEST_BINANCE_API, keys.TEST_BINANCE_SECRET)
socket = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"

ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()