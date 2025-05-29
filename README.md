# binancePump

Binance Pump Detector 

## What is this?

Creates a binance web socket and listen for trades. Aggragetes information, groups trade information via price, ticks and volume.
prints out at the time interval most traded, price changed and volume changed symbol.
This information could be detected an anomaly. An anomaly in binance could be leading to pump or dump.

Also it is working as a telegram bot here https://t.me/BinancePump_Bot

## How to run

```
$ git clone https://github.com/ogu83/binancePump.git
$ pip3 install termcolor joblib tqdm numpy pandas python-binance pyTelegramBotAPI
$ python3 binancePump.py

```

## Screen Shot

![Screenshot](binancePumpterminal.png)
