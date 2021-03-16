from binance.client import Client
from binance.enums import *
from datetime import datetime
import time
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
        # new_free_usdt = float(client.get_asset_balance(asset=settings.QUOTE)['free'])
        # free_bnb = float(client.get_asset_balance(asset=settings.BASE)['free'])
        free_usdt = new_free_usdt
        print("Free {} is {}, free {} is {}".format(settings.QUOTE,new_free_usdt,settings.BASE,free_bnb))
        print("Entry price is {} {}".format(entry_price,settings.QUOTE))

        return entry_price, free_usdt
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
        # precision_entry_price = precision_price(entry_price)
        precision_entry_price = "{:0.0{}f}".format(entry_price, settings.PRICE_FILTER)
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
        return False
    except Exception as e:
        print("Take order error: {}".format(e))
        return True

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
        return False
    except Exception as e:
        print("Stop order error: {}".format(e))
        return True

def get_margin_account_quote_balance(client):
    try:
        account = client.get_isolated_margin_account(symbols=settings.SYMBOL)
        if len(account['assets']) == 0:
            print("There is no isolated margin account {}. Need to create it".format(settings.SYMBOL))
            return 0
        else:
            if float(account['assets'][0]['quoteAsset']['borrowed']) == 0:
                quote_balance = float(account['assets'][0]['quoteAsset']['netAsset'])
                print("Quote net balance is {} {}".format(quote_balance,settings.QUOTE))
                return quote_balance 
            else:
                print("Quote borrowed > 0")
                return 0
    except Exception as e:
        print("Margin account balance error: {}".format(e))
        return 0

def create_qoute_loan(client,quote_net_balance):
    try:
        amount = quote_net_balance*settings.LEVER
        transaction = client.create_margin_loan(asset=settings.QUOTE,amount=amount,isIsolated='TRUE',symbol=settings.SYMBOL)
        if transaction['tranId'] > 0:
            account = client.get_isolated_margin_account(symbols=settings.SYMBOL)
            quote_loan = float(account['assets'][0]['quoteAsset']['borrowed'])
            quote_free = float(account['assets'][0]['quoteAsset']['free'])
            print("Loan {} is {}, free {} is {}".format(settings.QUOTE,quote_loan,settings.QUOTE,quote_free))
            return quote_free
    except Exception as e:
        print("Create quote loan error: {}".format(e))

def calc_base_quantity(client,quote_free_balance):
    try:
        trades = client.get_recent_trades(symbol=settings.SYMBOL,limit=1)
        last_quote_price = float(trades[-1]['price'])
        base_quantity = quote_free_balance/last_quote_price
        base_quantity_round = "{:0.0{}f}".format(base_quantity,settings.LOT_SIZE)
        print("Base quantity is {} {}".format(base_quantity_round,settings.BASE))
        return base_quantity_round
    except Exception as e:
        print("Calc base quantity error: {}".format(e))

def margin_buy(client,price):
    try:
        quote_net_balance = get_margin_account_quote_balance(client)
        quote_free_balance = create_qoute_loan(client,quote_net_balance)
        base_quantity = calc_base_quantity(client,quote_free_balance)
        base_price = "{:0.0{}f}".format(price, settings.PRICE_FILTER)
        print("Marging buying {} {} at {} {}".format(base_quantity,settings.BASE,base_price,settings.QUOTE))
        order = client.create_margin_order(
            symbol=settings.SYMBOL,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            quantity=base_quantity,
            timeInForce=TIME_IN_FORCE_GTC,
            price=base_price,
            isIsolated='TRUE')
        print("Margin buy order info: {}".format(order))
        return True
    except Exception as e:
        print("Margin buy order error: {}".format(e))
        return False

def repay_quote_loan(client):
    try:
        account = client.get_isolated_margin_account(symbols=settings.SYMBOL)
        borrowed = float(account['assets'][0]['quoteAsset']['borrowed'])
        interest = float(account['assets'][0]['quoteAsset']['interest'])
        amount = borrowed+interest
        transaction = client.repay_margin_loan(asset=settings.QUOTE,amount=amount,isIsolated='TRUE',symbol=settings.SYMBOL)
        if transaction['tranId'] > 0:
            account = client.get_isolated_margin_account(symbols=settings.SYMBOL)
            borrowed = float(account['assets'][0]['quoteAsset']['borrowed'])
            net_balance = float(account['assets'][0]['quoteAsset']['netAsset'])
            if borrowed == 0:
                print("Repay is finished. Total net balance is {} {}".format(net_balance,settings.QUOTE))
                return net_balance
            else:
                print("Something wrong. Borrowed is {} {}".format(borrowed,settings.QUOTE))
                return 0
    except Exception as e:
        print("Repay quoat loan error: {}".format(e))
        return 0

def margin_take(client,quantity,open_price,free_usdt):
    try:
        account_info = client.get_isolated_margin_account(symbols=settings.SYMBOL)
        base_free_balance = float(account_info['assets'][0]['baseAsset']['free'])
        print("Margin take order. Open price is {} {}. Selling {} {}".format(open_price,settings.QUOTE,base_free_balance,settings.BASE))
        order = client.create_margin_order(
            symbol=settings.SYMBOL,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            # timeInForce=TIME_IN_FORCE_GTC,
            quantity=base_free_balance,
            # price='0.00001',
            isIsolated='TRUE')
        time.sleep(3)
        new_free_usdt = repay_quote_loan(client)
        print("Profit is {} {}".format(new_free_usdt-free_usdt,settings.QUOTE))
        free_usdt = new_free_usdt
        print("Margin take order info: {}".format(order))
        return False
    except Exception as e:
        print("Margin take order error: {}".format(e))
        return True

def margin_stop(client,quantity,open_price,free_usdt):
    try:
        account_info = client.get_isolated_margin_account(symbols=settings.SYMBOL)
        base_free_balance = float(account_info['assets'][0]['baseAsset']['free'])
        print("Margin stop order. Open price is {} {}. Selling {} {}".format(open_price,settings.QUOTE,base_free_balance,settings.BASE))
        order = client.create_margin_order(
            symbol=settings.SYMBOL,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            # timeInForce=TIME_IN_FORCE_GTC,
            quantity=base_free_balance,
            # price='0.00001',
            isIsolated='TRUE')
        time.sleep(3)
        new_free_usdt = repay_quote_loan(client)
        print("Loss is {} {}".format(free_usdt-new_free_usdt,settings.QUOTE))
        free_usdt = new_free_usdt
        print("Margin stop order info: {}".format(order))
        return False
    except Exception as e:
        print("Margin stop order error: {}".format(e))
        return True

