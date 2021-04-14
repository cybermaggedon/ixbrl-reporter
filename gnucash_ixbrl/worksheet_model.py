
class WorksheetItem:
    pass

class SimpleValue(WorksheetItem):
    def __init__(self, defn, desc, value):
        self.defn = defn
        self.description = desc
        self.value = value

class Breakdown(WorksheetItem):
    def __init__(self, defn, desc, value, items):
        self.defn = defn
        self.description = desc
        self.value = value
        self.items = items

class NilValue(WorksheetItem):
    def __init__(self, defn, desc, value):
        self.defn = defn
        self.description = desc
        self.value = value

class Total(WorksheetItem):
    def __init__(self, defn, desc, value, items):
        self.defn = defn
        self.description = desc
        self.value = value
        self.items = items

class Worksheet:
    pass
