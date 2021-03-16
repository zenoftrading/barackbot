import websocket, json
import source as src
import settings

is_candle_opened = True
in_position = False
entry_price = 9999999.
quantity = 0.1
free_usdt = 0

def on_message(ws, msg):
    """Main algo function

    Args:
        ws: websocket
        msg: websocket message
    """
    global is_candle_opened, in_position, entry_price, quantity, free_usdt

    try:
        json_message = json.loads(msg)
        candle = json_message['k']
        is_candle_closed = candle['x']
        if is_candle_opened:
            if in_position:
                # stop or take
                if float(candle['o']) > entry_price:
                    free_usdt = src.take(settings.TEST_CLIENT,quantity,candle['o'],free_usdt)
                    in_position = False
                elif float(candle['o']) <= entry_price:
                    free_usdt = src.stop(settings.TEST_CLIENT,quantity,candle['o'],free_usdt)
                    in_position = False
            entry_price = src.on_the_opening_candle(settings.CLIENT,settings.TEST_CLIENT,quantity,free_usdt)
            is_candle_opened = False

        # check entry price
        if not in_position and float(candle['h']) >= entry_price:
            in_position = src.buy(settings.TEST_CLIENT,entry_price,quantity)

        if is_candle_closed:
            is_candle_opened = True

        src.print_current_candle(candle)
    except Exception as e:
        print("Websocket stream error: {}".format(e))

ws = websocket.WebSocketApp(settings.SOCKET, on_open=src.on_open, on_close=src.on_close, on_message=on_message)
ws.run_forever()