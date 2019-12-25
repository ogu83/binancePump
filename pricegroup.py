import datetime as dt
from datetime import datetime, timedelta
import time
from termcolor import colored
 
class PriceGroup:
    def __init__(self, 
            symbol, 
            tick_count,
            total_price_change, 
            relative_price_change,
            total_volume_change, 
            last_price,
            last_event_time,
            open, 
            volume,
            isPrinted):                
        self.symbol = symbol
        self.tick_count = tick_count 
        self.total_price_change = total_price_change
        self.relative_price_change = relative_price_change
        self.total_volume_change = total_volume_change
        self.last_price = last_price
        self.last_event_time = last_event_time
        self.open = open,
        self.volume = volume
        self.isPrinted = isPrinted

    def __repr__(self):
        return repr(self.symbol, 
                    self.tick_count, 
                    self.total_price_change, 
                    self.total_volume_change, 
                    self.relative_price_change,
                    self.last_price, 
                    self.last_event_time, 
                    self.open, 
                    self.volume,
                    self.isPrinted)

    def __getitem__(self, key):
        return getattr(self,key)    

    def to_string(self, isColored):
        self.isPrinted = True
        retval = "Symbol:{}\t Time:{}\t Ticks:{}\t RPCh:{}\t TPCh:{}\t VCh:{}\t LP:{}\t LV:{}\t".format(
                self.symbol,
                self.last_event_time,
                self.tick_count,
                "{0:2.2f}".format(self.relative_price_change),
                "{0:2.2f}".format(self.total_price_change),                
                "{0:2.2f}".format(self.total_volume_change),
                self.last_price,
                self.volume            
                )
        if (not isColored):
            return retval
        else:
            return colored(retval, self.console_color)

    @property
    def console_color(self):
        if self.relative_price_change < 0:
            return 'red'
        else:
            return 'green'
