
# Table
#   Array of Column
#     array (span, fact, Columns | None)
#   Index
#     Index (span, fact, Index | Series
#     IndexColumn

class Notable:
    def __init__(self):
        self.notes = None
    def set_notes(self, note):
        self.notes = note
    def has_notes(self):
        return self.notes is not None
    def get_notes(self):
        return self.notes

class Cell:
    def __init__(self, value):
        self.value = value

class Row:
    # values is an array of cell
    def __init__(self, values):
        self.values = values

class Index(Notable):
    # child is either a row, or an array of Index
    def __init__(self, metadata, child, notes=None):
        self.metadata = metadata
        self.child = child
        self.notes = notes

    def row_count(self):
        if isinstance(self.child, Row):
            return 1
        else:
            c = 0
            for ix in self.child:
                c += ix.row_count()
            return c

    def ix_levels(self):
        if isinstance(self.child, Row): return 1
        
        return 1 + max([ix.ix_levels() for ix in self.child])

    def recurse(self, fn, level=0):
        fn(self, level)
        if isinstance(self.child, Row):
            return
        for ix in self.child:
            ix.recurse(fn, level + 1)

    def has_notes(self):
        if self.notes is not None:
            return True
        if isinstance(self.child, list):
            for ix in self.child:
                if ix.has_notes():
                    return True
        return False

class TotalIndex(Index):
    pass

class Column:
    # children is either None or an array of Column
    def __init__(self, metadata, children=None, units=None):
        self.metadata = metadata
        self.children = children
        self.units = units
    def column_count(self):
        if self.children:
            c = 0
            for col in self.children:
                c += col.column_count()
            return c
        else:
            return 1
    def header_levels(self):
        if self.children == None:
            return 1
        else:
            return 1 + max([col.header_levels() for col in self.children])

    def recurse(self, fn, level=0):
        fn(self, level)
        if self.children:
            for col in self.children:
                col.recurse(fn, level + 1)

class Table:
    def __init__(self, columns, ixs):
        self.columns = columns
        self.ixs = ixs

    def column_count(self):
        c = 0
        for col in self.columns:
            c += col.column_count()
        return c

    def row_count(self):
        c = 0
        for ix in self.ixs:
            c += ix.row_count()
        return c

    def ix_levels(self):
        return max([ix.ix_levels() for ix in self.ixs])

    def header_levels(self):
        return max([col.header_levels() for col in self.columns])

    def column_recurse(self, fn):
        for col in self.columns:
            col.recurse(fn)

    def index_recurse(self, fn):
        for ix in self.ixs:
            ix.recurse(fn)

    def has_notes(self):
        for ix in self.ixs:
            if ix.has_notes():
                return True
        return False
