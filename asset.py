class Asset:
    def __init__(self, amount, symbol = 'TLOS'):
        self.symbol = symbol
        self.amount = amount

    def __str__(self):
        return ('%s %s') % (format(str(self.amount), '.4f'), self.symbol)