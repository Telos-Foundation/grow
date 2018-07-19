class Asset:
    def __init__(self, amount, symbol='TLOS'):
        self.symbol = symbol
        self.amount = amount

    def __str__(self):
        return ('%s %s') % (str.format(str(self.amount), '.4f'), self.symbol)

if __name__ == '__main__':
    a = Asset(1000)
    print(a)