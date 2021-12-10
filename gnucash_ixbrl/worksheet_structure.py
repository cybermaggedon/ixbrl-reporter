
from . datum import *

class Dataset:
    def __init__(self, periods, sections):
        self.periods = periods
        self.sections = sections
    def has_notes(self):
        for sec in self.sections:
            if sec.has_notes(): return True
        return False

class Series:
    def __init__(self, metadata, values, rank=0):
        self.metadata = metadata
        self.values = values
        self.rank = rank

    def has_notes(self):
        if self.metadata.note:
            return True
        return False

class Heading:
    def __init__(self, metadata):
        self.metadata = metadata

    def has_notes(self):
        if self.metadata.note:
            return True
        return False

    def update(self, reporter, grid, periods):
        reporter.add_heading(grid, self, periods)

class Totals:
    def __init__(self, computation, results, super_total=False):
        self.id = None
        self.value = None
        self.metadata = computation.metadata
        self.super_total = super_total

        for result in results:
            comp_res = computation.get_output(result)
            comp_res.add_value(computation, result, self)

    def has_notes(self):
        if self.value.has_notes():
            return True
        return False

    def update(self, reporter, grid, periods):
        reporter.add_totals(grid, self, periods, self.super_total)

class Break:
    def update(self, reporter, grid, periods):
        reporter.add_break(grid)
    def has_notes(self):
        return False

class SingleLine:
    def __init__(self, computation, results):
        self.id = None
        self.value = None
        self.metadata = computation.metadata

        for result in results:
            comp_res = computation.get_output(result)
            comp_res.add_value(computation, result, self)

    def has_notes(self):
        if self.value.has_notes():
            return True
        return False

    def update(self, reporter, grid, periods):
        reporter.add_single_line(grid, self, periods)

class Item:
    def __init__(self, computation, results):
        self.id = None
        self.value = None
        self.metadata = computation.metadata

        # FIXME, what's this???
        self.super_total = False

        for result in results:
            comp_res = computation.get_output(result)
            comp_res.add_value(computation, result, self)

    def has_notes(self):
        if self.value.has_notes():
            return True
        return False

    def update(self, reporter, grid, periods):
        reporter.add_item(grid, self, periods)
