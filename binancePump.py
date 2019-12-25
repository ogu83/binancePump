import pandas as pd
import numpy as np

import dateparser
import pytz
import json

import datetime as dt
from datetime import datetime, timedelta
import time

from tqdm import tqdm as tqdm

import os
import joblib
import operator
from termcolor import colored

from binance.client import Client
from binance.enums import *
from binance.websockets import BinanceSocketManager

from pricechange import *
from binanceHelper import *
from pricegroup import *

show_limit = 3
min_perc = 0.01
price_changes = []
price_groups = {}

last_symbol = "X"

def process_message(tickers):
    # print("stream: {} data: {}".format(msg['stream'], msg['data']))
    # print("Len {}".format(len(msg)))
    # print("Currentb Price Of {} is {}".format(msg[0]['s'], msg[0]['c']))
    
    for ticker in tickers:
        symbol = ticker['s']
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
    #print(len(price_changes))
    
    for price_change in price_changes:
        console_color = 'green'
        if price_change.price_change_perc < 0:
            console_color = 'red'

        if (not price_change.isPrinted 
            and abs(price_change.price_change_perc) > min_perc 
            and price_change.volume_change_perc > min_perc):

            price_change.isPrinted = True
            #print(colored("Time:{} \t Sym:{} \t Ch:{}% \t VCh:{}% \t TT:{} \t PP:{} \t P:{} \t O:{} \t V:{}".format(
            #         price_change.event_time, 
            #         price_change.symbol, 
            #         "{0:2.2f}".format(price_change.price_change_perc), 
            #         "{0:2.2f}".format(price_change.volume_change_perc),
            #         price_change.total_trades,                
            #         price_change.prev_price, 
            #         price_change.price, 
            #         price_change.open,
            #         round(price_change.volume)), console_color))   
            
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
                price_groups[price_change.symbol].isPrinted = False
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
                    if not max_price_group.isPrinted:
                        if not header_printed:
                            print ("Top Ticks")
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
                    if not max_price_group.isPrinted:
                        if not header_printed:
                            print ("Top Total Price Change")
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
                    if not max_price_group.isPrinted:
                        if not header_printed:
                            print ("Top Relative Price Change")
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
                    if not max_price_group.isPrinted:
                        if not header_printed:
                            print ("Top Total Volume Change")
                            header_printed = True
                        print(max_price_group.to_string(True))
                        anyPrinted = True

        #max_price_group = max(price_groups, key=lambda k:price_groups[k]['tick_count'])
        #max_price_group = price_groups[max_price_group]
        #if not max_price_group.isPrinted:
        #    print ("Top Ticks")
        #    print(max_price_group.to_string())
        #    anyPrinted = True

        #max_price_group = max(price_groups, key=lambda k:price_groups[k]['total_price_change'])
        #max_price_group = price_groups[max_price_group]
        #if not max_price_group.isPrinted:
        #    print ("Top Total Price Change")
        #    print(max_price_group.to_string())
        #    anyPrinted = True

        #max_price_group = max(price_groups, key=lambda k:price_groups[k]['total_volume_change'])
        #max_price_group = price_groups[max_price_group]
        #if not max_price_group.isPrinted:
        #    print ("Top Total Volume Change")
        #    print(max_price_group.to_string())
        #    anyPrinted = True

        if anyPrinted:
            print("")

def main():
    api_config = {}
    with open('api_config.json') as json_data:
        api_config = json.load(json_data)
        json_data.close()    

    client = Client(api_config['api_key'], api_config['api_secret'])
    # prices = client.get_all_tickers()
    # pairs = list(pd.DataFrame(prices)['symbol'].values)
    # pairs = [pair for pair in pairs if 'BTC' in pair]
    # print(pairs)    
          
    bm = BinanceSocketManager(client)
    conn_key = bm.start_ticker_socket(process_message)
    bm.start()
    
    input("Press Enter to continue...")
    bm.stop_socket(conn_key)
    bm.close()
    print('Socket Closed')
    return
    
if __name__ == '__main__':
    main()
