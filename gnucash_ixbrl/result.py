
# The data model of a worksheet.  There are four kinds of thing which make
# up the output of a worksheet: Simple value, line-item breakdown,
# a total (without line-item breakdown), and a special nil value.

class Result:
    pass

class SimpleResult(Result):
    def __init__(self, defn, value):
        self.defn = defn
        self.value = value

class BreakdownResult(Result):
    def __init__(self, defn, value, items):
        self.defn = defn
        self.value = value
        self.items = items

class NilResult(Result):
    def __init__(self, defn, value):
        self.defn = defn
        self.value = value

class TotalResult(Result):
    def __init__(self, defn, value, items):
        self.defn = defn
        self.value = value
        self.items = items
