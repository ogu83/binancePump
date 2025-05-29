import pandas as pd
import numpy as np
import json
import datetime as dt
import operator
from binance.enums import *
from binance import ThreadedWebsocketManager
from pricechange import *
from binanceHelper import *
from pricegroup import *
import signal
import threading
import sys
from typing import Dict, List

show_only_pair = "USDT" #Select nothing for all, only selected currency will be shown
show_limit = 1      #minimum top query limit
min_perc = 0.05     #min percentage change
price_changes = []
price_groups: Dict[str, PriceGroup] = {}
last_symbol = "X"
chat_ids = []
twm = {}

def get_price_groups() -> List[PriceGroup]:
    """
    Returns a snapshot list of all current PriceGroup objects.
    """
    return list(price_groups.values())


def process_message(tickers):
    for ticker in tickers:
        symbol = ticker['s']

        if not show_only_pair in symbol:
            continue

        price = float(ticker['c'])
        total_trades = int(ticker['n'])
        open = float(ticker['o'])
        volume = float(ticker['v'])
        event_time = dt.datetime.fromtimestamp(int(ticker['E'])/1000)
        if len(price_changes) > 0:
            price_change = filter(lambda item: item.symbol == symbol, price_changes)
            price_change = list(price_change)
            if (len(price_change) > 0):
                price_change = price_change[0]
                price_change.event_time = event_time
                price_change.prev_price = price_change.price
                price_change.prev_volume = price_change.volume
                price_change.price = price
                price_change.total_trades = total_trades
                price_change.open = open
                price_change.volume = volume
                price_change.isPrinted = False
            else:
                price_changes.append(PriceChange(symbol, price, price, total_trades, open, volume, False, event_time, volume))
        else:
            price_changes.append(PriceChange(symbol, price, price, total_trades, open, volume, False, event_time, volume))

    price_changes.sort(key=operator.attrgetter('price_change_perc'), reverse=True)
    
    for price_change in price_changes:
        if (not price_change.isPrinted 
            and abs(price_change.price_change_perc) > min_perc 
            and price_change.volume_change_perc > min_perc):

            price_change.isPrinted = True 

            if not price_change.symbol in price_groups:
                price_groups[price_change.symbol] = PriceGroup(price_change.symbol,                                                                
                                                            1,                                                                
                                                            abs(price_change.price_change_perc),
                                                            price_change.price_change_perc,
                                                            price_change.volume_change_perc,                                                                
                                                            price_change.price,                                                                                                                             
                                                            price_change.event_time,
                                                            price_change.open,
                                                            price_change.volume,
                                                            False,
                                                            )
            else:
                price_groups[price_change.symbol].tick_count += 1
                price_groups[price_change.symbol].last_event_time = price_change.event_time
                price_groups[price_change.symbol].volume = price_change.volume
                price_groups[price_change.symbol].last_price = price_change.price
                price_groups[price_change.symbol].is_printed = False
                price_groups[price_change.symbol].total_price_change += abs(price_change.price_change_perc)
                price_groups[price_change.symbol].relative_price_change += price_change.price_change_perc
                price_groups[price_change.symbol].total_volume_change += price_change.volume_change_perc                

    if len(price_groups)>0:
        anyPrinted = False 
        sorted_price_group = sorted(price_groups, key=lambda k:price_groups[k]['tick_count'])
        if (len(sorted_price_group)>0):
            sorted_price_group = list(reversed(sorted_price_group))
            for s in range(show_limit):
                header_printed=False
                if (s<len(sorted_price_group)):
                    max_price_group = sorted_price_group[s]
                    max_price_group = price_groups[max_price_group]
                    if not max_price_group.is_printed:
                        if not header_printed:
                            msg = "Top Ticks"
                            print(msg)
                            header_printed = True
                        print(max_price_group.to_string(True))
                        anyPrinted = True

        sorted_price_group = sorted(price_groups, key=lambda k:price_groups[k]['total_price_change'])
        if (len(sorted_price_group)>0):
            sorted_price_group = list(reversed(sorted_price_group))
            for s in range(show_limit):
                header_printed=False
                if (s<len(sorted_price_group)):
                    max_price_group = sorted_price_group[s]
                    max_price_group = price_groups[max_price_group]
                    if not max_price_group.is_printed:
                        if not header_printed:
                            msg = "Top Total Price Change"
                            print(msg)
                            header_printed = True
                        print(max_price_group.to_string(True))
                        anyPrinted = True

        sorted_price_group = sorted(price_groups, key=lambda k:abs(price_groups[k]['relative_price_change']))
        if (len(sorted_price_group)>0):
            sorted_price_group = list(reversed(sorted_price_group))
            for s in range(show_limit):
                header_printed=False
                if (s<len(sorted_price_group)):
                    max_price_group = sorted_price_group[s]
                    max_price_group = price_groups[max_price_group]
                    if not max_price_group.is_printed:
                        if not header_printed:
                            msg = "Top Relative Price Change"
                            print(msg)
                            header_printed = True
                        print(max_price_group.to_string(True))
                        anyPrinted = True

        sorted_price_group = sorted(price_groups, key=lambda k:price_groups[k]['total_volume_change'])
        if (len(sorted_price_group)>0):
            sorted_price_group = list(reversed(sorted_price_group))
            for s in range(show_limit):
                header_printed=False
                if (s<len(sorted_price_group)):
                    max_price_group = sorted_price_group[s]
                    max_price_group = price_groups[max_price_group]
                    if not max_price_group.is_printed:
                        if not header_printed:
                            msg = "Top Total Volume Change"
                            print(msg)
                            header_printed = True
                        print(max_price_group.to_string(True))
                        anyPrinted = True

        if anyPrinted:
            print("")

def stop():
    twm.stop()

def main():
    #READ API CONFIG
    api_config = {}
    with open('api_config.json') as json_data:
        api_config = json.load(json_data)
        json_data.close()

    api_key = api_config['api_key']
    api_secret = api_config['api_secret']
    
#    Create an Event that signals “stop everything”
    stop_event = threading.Event()

    # Define our signal handler to set that event
    def handle_exit(signum, frame):
        print("\nShutting down…")
        stop_event.set()
        twm.stop()        # tells the Binance manager to stop

    # Catch SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Start the threaded websocket manager
    twm = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
    twm.start()
    twm.start_ticker_socket(process_message)
    
    print("Websocket running. Press Ctrl+C to exit.")

    # Now simply wait until we’re told to stop…
    stop_event.wait()

    print("Clean exit complete.")
    return
    
if __name__ == '__main__':
    main()