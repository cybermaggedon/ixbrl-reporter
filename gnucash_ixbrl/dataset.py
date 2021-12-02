
from . datum import *

class Dataset:
    def __init__(self, periods, sections):
        self.periods = periods
        self.sections = sections
    def has_notes(self):
        for sec in self.sections:
            if sec.has_notes(): return True
        return False
        

class Section:
    def __init__(self):
        self.id = None
        self.metadata = None
        self.items = None
        self.total = None

    def add_data(self, computation, comp_def, results):

        self.metadata = computation.metadata

        for result in results:
            comp_res = computation.get_output(result)
            comp_res.add_data(computation, comp_def, result, self)

    def has_notes(self):
        if self.total.has_notes():
            return True
        if self.items:
            for item in self.items:
                if item.has_notes(): return True
        return False

class Series:
    def __init__(self, metadata, values, rank=0):
        self.metadata = metadata
        self.values = values
        self.rank = rank

    def has_notes(self):
        print(self.metadata)
        if self.metadata.note:
            return True
        return False
