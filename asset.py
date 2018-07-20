class Asset:
    def __init__(self, amount, symbol = 'TLOS'):
        self.symbol = symbol
        self.amount = amount

    def __str__(self):
        return ('%s %s') % ('%.4f'%(self.amount), self.symbol)
