
# The data model of a worksheet.  There are four kinds of thing which make
# up the output of a worksheet: Simple value, line-item breakdown,
# a total (without line-item breakdown), and a special nil value.

from . dataset import *

class WorksheetItem:
    pass

class WsStructure:
    def __init__(self):
        pass

class SimpleValue(WorksheetItem):
    def __init__(self, defn, desc, value):
        self.defn = defn
        self.description = desc
        self.value = value
    def add_data(self, computation, cdef, result, sec):
        raise RuntimeError("Not implemented")

class Breakdown(WorksheetItem):
    def __init__(self, defn, desc, value, items):
        self.defn = defn
        self.description = desc
        self.value = value
        self.items = items

    def add_data(self, computation, cdef, result, sec):

        if sec.header == None:
            sec.header = computation.description

        if sec.total == None:
            sec.total = Series("Total", [], rank=cdef.total_rank)

        if sec.items == None:
            sec.items = [
                Series(computation.inputs[i].description, [],
                       rank=cdef.rank)
                for i in range(0, len(computation.inputs))
            ]

        sec.total.values.append(self.value.value)

        for i in range(0, len(computation.inputs)):
            id = computation.inputs[i].id
            value = result[computation.id].items[i].value
            sec.items[i].values.append(value)

class NilValue(WorksheetItem):
    def __init__(self, defn, desc, value):
        self.defn = defn
        self.description = desc
        self.value = value
    def add_data(self, computation, cdef, result, sec):

        if sec.header == None:
            sec.header = computation.description

        if sec.total == None:
            sec.total = Series("Total", [], rank=cdef.total_rank)

        sec.total.values.append(self.value.value)

class Total(WorksheetItem):

    def __init__(self, defn, desc, value, items):
        self.defn = defn
        self.description = desc
        self.value = value
        self.items = items

    def add_data(self, computation, cdef, result, sec):

        if sec.header == None:
            sec.header = computation.description

        if sec.total == None:
            sec.total = Series("Total", [], rank=cdef.total_rank)

        sec.total.values.append(self.value.value)

class Worksheet:
    pass
