
# This is generic context management.  Inside ixbrl-reporter, contexts are
# managed in a taxonomy-free way, structured in terms of entities, time periods,
# and segments.  The taxonomy maps these taxonomy-free contexts into the real
# tags.

from . datum import *

class Context:
    def __init__(self, parent):
        self.parent = parent
        self.entity = None
        self.scheme = None
        self.segments = {}
        self.period = None
        self.instant = None
        self.children = {}

    def get_hash(self):
        return "@@".join(
            [
                ",".join(v)
                for v in self.get_dimensions()
            ]
        )

    def get_dimensions(self):
        if self.parent:
            dims = self.parent.get_dimensions()
        else:
            dims  = []
        if self.entity:
            dims.append(("entity", self.scheme, self.entity))
        if self.segments:
            for k, v in self.segments:
                dims.append(("segment", k, v))
        if self.period:
            dims.append(("period", str(self.period.start),
                         str(self.period.end)))
        if self.instant:
            dims.append(("instant", str(self.instant)))
        return dims

    def with_segment(self, k, v):
        return self.with_segments(((k, v)))

    def with_segments(self, segments):

        # entity, scheme, segments, period, instant
        seghash = "//".join([
            "%s=%s" % (k, v)
            for k, v in segments
        ])
        k = (None, None, seghash, None, None)
        if k in self.children:
            return self.children[k]

        c = Context(self)
        self.children[k] = c
        c.segments = segments
        return c

    def with_period(self, period):

        # entity, scheme, segments, period, instant
        k = (None, None, None, str(period), None)
        if k in self.children:
            return self.children[k]

        c = Context(self)
        self.children[k] = c
        c.period = period
        return c

    def with_instant(self, instant):

        # entity, scheme, segments, period, instant
        k = (None, None, None, None, str(instant))
        if k in self.children:
            return self.children[k]

        c = Context(self)
        self.children[k] = c
        c.instant = instant
        return c

    def with_entity(self, scheme, id):

        # entity, scheme, segments, period, instant
        k = (id, scheme, None, None, None)
        if k in self.children:
            return self.children[k]

        c = Context(self)
        self.children[k] = c
        c.entity = id
        c.scheme = scheme
        return c

    def describe(self):
        if self.parent:
            self.parent.describe()
        if self.entity:
            print("Entity: %s (%s)" % (self.entity, self.scheme))
        if self.segments:
            for k, v in self.segments.items():
                print("Segment: %s (%s)" % (k, v))
        if self.period:
            print("Period: %s" % self.period)

    def create_money_datum(self, id, value):
        return MoneyDatum(id, value, self)

