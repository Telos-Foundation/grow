class Asset:
    def __init__(self, amount, symbol = 'TLOS'):
        self.symbol = symbol
        self.amount = amount

    def __str__(self):
        return ('%s %s') % ('{0:.2f}'.format(str(self.amount)), self.symbol)