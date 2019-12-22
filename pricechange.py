class PriceChange:
    def __init__(self, symbol,prev_price, price):
        self.symbol = symbol
        self.prev_price = prev_price
        self.price = price
    def __repr__(self):
        return repr((self.symbol, self.prev_price, self.price))
    
    @property
    def price_change(self):
        return self.price-self.prev_price

    @property
    def price_change_perc(self):
        return self.price_change / self.prev_price * 100

    def IsPump(self,lim_perc):
        return self.price_change_perc() >= lim_perc
    def IsDump(self,lim_perc):
        if (lim_perc > 0):
            lim_perc = -1*lim_perc
        return self.price_change_perc() <= lim_perc

