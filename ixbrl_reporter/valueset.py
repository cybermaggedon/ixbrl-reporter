
# A ValueSet is a set of values referenced by id.

from . config import StringValue, NoneValue
from . datum import *

class ValueSet:
    def __init__(self):
        self.values = {}
    def add_money(self, id, value, c):
        self.values[id] = MoneyDatum(id, value, c)
    def add_string(self, id, value, c):
        self.values[id] = StringDatum(id, value, c)
    def add_count(self, id, value, c):
        self.values[id] = CountDatum(id, value, c)
    def add_bool(self, id, value, c):
        self.values[id] = BoolDatum(id, value, c)
    def add_date(self, id, value, c):
        self.values[id] = DateDatum(id, value, c)
    def add_datum(self, datum):
        self.values[datum.id] = datum
    def get(self, id):
        if id in self.values:
            return self.values[id]
        else:
            return NoneDatum(id)
