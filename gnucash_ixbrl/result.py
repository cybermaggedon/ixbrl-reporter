
# The data model of a worksheet.  There are four kinds of thing which make
# up the output of a worksheet: Simple value, line-item breakdown,
# a total (without line-item breakdown), and a special nil value.

from . worksheet_structure import Series

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

    def add_total(self, computation, result, sec):

        if sec.metadata == None:
            sec.metadata = computation.metadata

        if sec.total == None:
            sec.total = Series(self.defn.metadata, [])

        sec.total.values.append(self.value)

    def add_value(self, computation, result, sec):

        if sec.metadata == None:
            sec.metadata = computation.metadata

        if sec.value == None:
            sec.value = Series(computation.metadata, [])

        sec.value.values.append(self.value)

class NilResult(Result):
    def __init__(self, defn, value):
        self.defn = defn
        self.value = value

    def add_total(self, computation, result, sec):

        if sec.metadata == None:
            sec.metadata = computation.metadata

        if sec.total == None:
            sec.total = Series(self.defn.metadata, [])

        sec.total.values.append(self.value)

    def add_value(self, computation, result, sec):

        if sec.metadata == None:
            sec.metadata = computation.metadata

        if sec.value == None:
            sec.value = Series(self.defn.metadata, [])

        sec.value.values.append(self.value)

    def add_items(self, computation, result, sec):
        pass

class TotalResult(Result):

    def __init__(self, defn, value, items):
        self.defn = defn
        self.value = value
        self.items = items

    def add_total(self, computation, result, sec):

        if sec.metadata == None:
            sec.metadata = computation.metadata

        if sec.total == None:
            sec.total = Series(self.defn.metadata, [])

        sec.total.values.append(self.value)

    def add_value(self, computation, result, sec):

        if sec.metadata == None:
            sec.metadata = computation.metadata

        if sec.value == None:
            sec.value = Series(self.defn.metadata, [])

        sec.value.values.append(self.value)

    def add_items(self, computation, result, sec):
        pass

