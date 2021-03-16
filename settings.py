from binance.client import Client
from binance.enums import *
import source as src
import keys

BINANCE_API = ''
BINANCE_SECRET = ''

TEST_BINANCE_API = ''
TEST_BINANCE_SECRET = ''

# for testnet trading
TEST_CLIENT = Client(TEST_BINANCE_API, TEST_BINANCE_SECRET)
TEST_CLIENT.API_URL = 'https://testnet.binance.vision/api'
# test_socket = "wss://testnet.binance.vision/ws/bnbusdt@kline_1m"

# for real trading and prices
CLIENT = Client(BINANCE_API, BINANCE_SECRET)
SOCKET = "wss://stream.binance.com:9443/ws/bnbusdt@kline_1m"

# global variables
BASE = "BNB"
QUOTE = "USDT"
SYMBOL = BASE+QUOTE
LEVER = 2

def get_symbol_limits(client,symbol):
    try:
        info = client.get_symbol_info(symbol)
        price_filter = str(float(info['filters'][0]['minPrice']))[::-1].find('.')
        lot_size = str(float(info['filters'][2]['minQty']))[::-1].find('.')
        min_notional = float(info['filters'][3]['minNotional'])
        print("{} price filter {}, lot size {}, min notional {}".format(symbol,price_filter,lot_size,min_notional))
        return price_filter, lot_size, min_notional
    except Exception as e:
        print("get_symbol_limits error: {}".format(e))
        return 0, 0, 0


PRICE_FILTER, LOT_SIZE, MIN_NOTIONAL = get_symbol_limits(CLIENT,SYMBOL)