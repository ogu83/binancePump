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

min_perc = 0.01
price_changes = []

last_symbol = "X"

def binanceDataFrame(klines):
    df = pd.DataFrame(klines.reshape(-1,12),dtype=float, columns = ('Open Time',
                                                                    'Open',
                                                                    'High',
                                                                    'Low',
                                                                    'Close',
                                                                    'Volume',
                                                                    'Close Time',
                                                                    'Quote asset volume',
                                                                    'Number of trades',
                                                                    'Taker buy base asset volume',
                                                                    'Taker buy quote asset volume',
                                                                    'Ignore'))

    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df['Close Time'] = pd.to_datetime(df['Close Time'], unit='ms')

    return df

def date_to_milliseconds(date_str):
    """Convert UTC date to milliseconds
    If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/
    :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
    :type date_str: str
    """
    # get epoch value in UTC
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d = dateparser.parse(date_str)
    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)

def interval_to_milliseconds(interval):
    """Convert a Binance interval string to milliseconds
    :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
    :type interval: str
    :return:
         None if unit not one of m, h, d or w
         None if string not in correct format
         int value of interval in milliseconds
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms

def get_historical_klines(symbol, interval, start_str, end_str=None):
    """Get Historical Klines from Binance
    See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/
    If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Biannce Kline interval
    :type interval: str
    :param start_str: Start date string in UTC format
    :type start_str: str
    :param end_str: optional - end date string in UTC format
    :type end_str: str
    :return: list of OHLCV values
    """
    # create the Binance client, no need for api key    

    # init our list
    output_data = []

    # setup the max limit
    limit = 500

    # convert interval to useful value in seconds
    timeframe = interval_to_milliseconds(interval)

    # convert our date strings to milliseconds
    start_ts = date_to_milliseconds(start_str)

    # if an end time was passed convert it
    end_ts = None
    if end_str:
        end_ts = date_to_milliseconds(end_str)

    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set
        temp_data = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_ts,
            endTime=end_ts
        )

        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True

        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(1)

    return output_data

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

        if (not price_change.isPrinted and abs(price_change.price_change_perc) > min_perc and price_change.volume_change_perc > min_perc):
            price_change.isPrinted = True
            print(colored("Time:{} \t Sym:{} \t Ch:{}% \t VCh:{}% \t TT:{} \t PP:{} \t P:{} \t O:{} \t V:{}".format(
                     price_change.event_time, 
                     price_change.symbol, 
                     "{0:2.2f}".format(price_change.price_change_perc), 
                     "{0:2.2f}".format(price_change.volume_change_perc),
                     price_change.total_trades,                
                     price_change.prev_price, 
                     price_change.price, 
                     price_change.open,
                     round(price_change.volume)), console_color))        
    
    # if ((price_changes[0].price_change_perc > min_perc) and not price_changes[0].isPrinted):
        # price_changes[0].isPrinted = True
        # print("Time:{}\tSym:{}\tCh:{}%\tT:{}\tPP:{}\tP:{}\tO:{}\tV:{}\t".format(
                # price_changes[0].event_time, 
                # price_changes[0].symbol, 
                # "{0:2.2f}".format(price_changes[0].price_change_perc), 
                # price_changes[0].total_trades,                
                # price_changes[0].prev_price, 
                # price_changes[0].price, 
                # price_changes[0].open,
                # round(price_changes[0].volume)
                # ))


    # last_index = len(price_changes)-1
    # if ((price_changes[last_index].price_change_perc < -min_perc) and not price_changes[last_index].isPrinted):
        # price_changes[last_index].isPrinted = True
        # print(colored("Time:{}\tSym:{}\tCh:{}%\tT:{}\tPP:{}\tP:{}\tO:{}\tV:{}\t".format(
                # price_changes[last_index].event_time, 
                # price_changes[last_index].symbol, 
                # "{0:2.2f}".format(price_changes[last_index].price_change_perc), 
                # price_changes[last_index].total_trades,                
                # price_changes[last_index].prev_price, 
                # price_changes[last_index].price, 
                # price_changes[last_index].open,
                # round(price_changes[last_index].volume)
                # ),'red'))

def main():
    api_config = {}
    with open('api_config.json') as json_data:
        api_config = json.load(json_data)
        json_data.close()    

    client = Client(api_config['api_key'], api_config['api_secret'])
    prices = client.get_all_tickers()
    pairs = list(pd.DataFrame(prices)['symbol'].values)
    pairs = [pair for pair in pairs if 'BTC' in pair]
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
