from binance.client import Client
from binance.enums import *

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
