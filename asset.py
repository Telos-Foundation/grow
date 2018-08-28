class Asset:
    def __init__(self, amount, symbol='TLOS'):
        self.symbol = symbol
        self.amount = amount

    def __str__(self):
        return ('%s %s') % ('%.4f'%(self.amount), self.symbol)

    @staticmethod
    def string_to_asset(string):
        array = string.split(' ')
        return Asset(float(array[0]), str(array[1]))

    def __add__(self, other):
        return Asset(self.amount + other.amount)

    def __sub__(self, other):
        return Asset(self.amount - other.amount)

    def __iadd__(self, other):
        return Asset(self.amount + other.amount)