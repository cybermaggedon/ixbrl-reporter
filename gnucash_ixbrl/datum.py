
# A datum is representation of a data value in a taxonomy-free way.  A datum
# has an identifier e.g. company-name, a value and a context.
class Datum:
    def describe(self):
        print("%-20s: %s" % (self.id, str(self.value)))
    def use(self, fn):
        fn(self)

class MoneyDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

class NoneDatum(Datum):
    def __init__(self, id):
        self.id = id
    def use(self, fn):
        pass

class StringDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

class CountDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

class NumberDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

class BoolDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

class DateDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

class VariableDatum(Datum):
    def __init__(self, id, value, context):
        self.id = id
        self.value = value
        self.context = context

