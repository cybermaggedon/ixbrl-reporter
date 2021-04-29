
# Computations used to compute values from GnuCash accounts.
import json
import datetime
import uuid

from . worksheet_model import SimpleValue, Breakdown, NilValue, Total
from . period import Period

def get_computation(item, comps, context, data):
    if isinstance(item, str):
        return comps[item]
    return Computable.load(item, comps, context, data)

def create_uuid():
    return str(uuid.uuid4())

IN_YEAR = 1
AT_START = 2
AT_END = 3

class Computable:
    def compute(self, accounts, start, end, result):
        raise RuntimeError("Not implemented")

    @staticmethod
    def load(cfg, comps, context, data):

        kind = cfg.get("kind")

        if kind == "group":
            return Group.load(cfg, comps, context, data)

        if kind == "sum":
            return Sum.load(cfg, comps, context, data)

        if kind == "apportion":
            return ApportionOperation.load(cfg, comps, context, data)

        # For UK corporation tax.  >:-O
        if kind == "round":
            return RoundOperation.load(cfg, comps, context, data)

        if kind == "factor":
            return FactorOperation.load(cfg, comps, context, data)

        if kind == "line":
            return Line.load(cfg, comps, context, data)

        if kind == "constant":
            return Constant.load(cfg, comps, context, data)

        raise RuntimeError("Don't understand computable type '%s'" % kind)

class Line(Computable):

    def __init__(self, id, description, accounts, context, period=AT_END,
                 reverse=False, segments={}):
        self.id = id
        self.description = description
        self.accounts = accounts
        self.context = context
        self.period = period
        self.reverse = reverse
        self.segments = segments

    @staticmethod
    def load(cfg, comps, context, data):
        id = cfg.get("id", None, mandatory=False)
        if id == None: id = create_uuid()

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        segs = cfg.get("segments", {})

        return Line(id, cfg.get("description", "?"), cfg.get("accounts"),
                    context, pid, cfg.get_bool("reverse-sign", False), segs)

    def compute(self, session, start, end, result):

        total = 0

        # FIXME: If there are transactions preceding 1970, this won't work.
        if self.period == AT_START:
            context = self.context.with_instant(start)
            history = datetime.date(1970, 1, 1)
            start, end = history, start
        elif self.period == AT_END:
            context = self.context.with_instant(end)
            history = datetime.date(1970, 1, 1)
            start, end = history, end
        else:
            context = self.context.with_period(Period("", start, end))
            
        for acct_name in self.accounts:
            acct = session.get_account(session.root, acct_name)

            splits = session.get_splits(acct, start, end)

            acct_total = sum([v["amount"] for v in splits])

            if session.is_debit(acct.GetType()):
                acct_total *= -1

            total += acct_total

        if self.reverse: total *= -1

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        result.set(self.id, context.create_money_datum(self.id, total))

        return total

    def get_output(self, result):

        if len(self.accounts) == 0:
            output = NilValue(self, self.description, result.get(self.id))
            return output

        output = Total(self, self.description, result.get(self.id),
                       items=[])

        return output

class Constant(Computable):
    def __init__(self, id, description, values, context, period=AT_END,
                 segments={}):
        self.id = id
        self.description = description
        self.values = values
        self.context = context
        self.period = period
        self.segments = segments

    @staticmethod
    def load(cfg, comps, context, data):
        id = cfg.get("id")
        if id == None: id = create_uuid()

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        segs = cfg.get("segments", {})

        return Constant(id, cfg.get("description", "?"), cfg.get("values"),
                        context, pid, segs)

    def compute(self, session, start, end, result):

        if self.period == AT_START:
            context = self.context.with_instant(start)
            cdef.set_instant(start, end)
        elif self.period == AT_END:
            context = self.context.with_instant(end)
            cdef.set_period(end)
        else:
            context = self.context.with_period(Period("", start, end))

        val = self.values[str(end)]

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        result.set(self.id, context.create_money_datum(self.id, val))

        return val

    def get_output(self, result):

        output = SimpleValue(self, self.description, result.get(self.id))

        return output

class Group(Computable):
    def __init__(self, id, description, inputs=None, context=None,
                 period=AT_END, segments={}):

        if inputs == None:
            inputs = []

        self.id = id
        self.description = description
        self.inputs = inputs
        self.context = context
        self.period = period
        self.segments = segments

    @staticmethod
    def load(cfg, comps, context, data):

        id = cfg.get("id", None, mandatory=False)
        if id == None: id = create_uuid()

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        segs = cfg.get("segments", {})

        comp = Group(id, cfg.get("description", "?"), [], context, pid, segs)

        for item in cfg.get("inputs"):
            comp.add(get_computation(item, comps, context, data))

        def set_hide(x):
            comp.hide_breakdown = x

        cfg.get("hide-breakdown", False).use(set_hide)
        
        return comp

    def add(self, input):
        self.inputs.append(input)

    def compute(self, accounts, start, end, result):

        if self.period == AT_START:
            context = self.context.with_instant(start)
        elif self.period == AT_END:
            context = self.context.with_instant(end)
        else:
            context = self.context.with_period(Period("", start, end))

        total = 0
        for input in self.inputs:
            total += input.compute(accounts, start, end, result)

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        result.set(self.id, context.create_money_datum(self.id, total))

        return total

    def get_output(self, result):

        if len(self.inputs) == 0:
            output = NilValue(self, self.description, result.get(self.id))
            return output

        if self.hide_breakdown:

            # For a hidden breakdown, create a breakdown object which is not
            # returned, and a Total object which references it
            bd = Breakdown(
                self,
                self.description,
                result.get(self.id),
                items= [
                    item.get_output(result) for item in self.inputs
                ]
            )

            output = Total(self, self.description, result.get(self.id),
                           items=[bd])

        else:

            output = Breakdown(
                self,
                self.description,
                result.get(self.id),
                items= [
                    item.get_output(result) for item in self.inputs
                ]
            )

        return output

class ApportionOperation(Computable):
    def __init__(self, id, description, context, period, segments,
                 item, part, whole):
        self.id = id
        self.description = description
        self.context = context
        self.period = period
        self.segments = segments
        self.item = item
        self.fraction = part.days() / whole.days()

    @staticmethod
    def load(cfg, comps, context, data):

        id = cfg.get("id", None, mandatory=False)
        if id == None: id = create_uuid()

        description = cfg.get("description", "?")
        whole_key = cfg.get("whole-period")
        whole = Period.load(data.get_config(whole_key))
        proportion_key = cfg.get("proportion-period")
        proportion = Period.load(data.get_config(proportion_key))
        segs = cfg.get("segments", {})

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        item = comps[cfg.get("input")]

        return ApportionOperation(id, description, context, pid, segs,
                                  item, proportion, whole)

    def compute(self, accounts, start, end, result):

        if self.period == AT_START:
            context = self.context.with_instant(start)
        elif self.period == AT_END:
            context = self.context.with_instant(start)
        else:
            context = self.context.with_period(Period("", start, end))

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        val = self.item.compute(accounts, start, end, result)
        val *= self.fraction

        result.set(self.id, context.create_money_datum(self.id, val))
        return val

    def get_output(self, result):

        output = Total(self, self.description, result.get(self.id),
                       items=[])

        return output

class RoundOperation(Computable):
    def __init__(self, id, description, context, period, segments, item):
        self.id = id
        self.description = description
        self.context = context
        self.period = period
        self.segments = segments
        self.item = item

    @staticmethod
    def load(cfg, comps, context, data):

        id = cfg.get("id", None, mandatory=False)
        if id == None: id = create_uuid()
        description = cfg.get("description", "?")
        segs = cfg.get("segments", {})

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        item = cfg.get("input")

        return RoundOperation(
            id, description, context, pid, segs,
            get_computation(item, comps, context, data)
        )

    def compute(self, accounts, start, end, result):

        if self.period == AT_START:
            context = self.context.with_instant(start)
        elif self.period == AT_END:
            context = self.context.with_instant(start)
        else:
            context = self.context.with_period(Period("", start, end))

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        val = self.item.compute(accounts, start, end, result)
        val = round(val)

        result.set(self.id, context.create_money_datum(self.id, val))
        return val

    def get_output(self, result):

        output = Total(self, self.description, result.get(self.id),
                       items=[])

        return output

class FactorOperation(Computable):
    def __init__(self, id, description, context, period, segments, item,
                 factor):
        self.id = id
        self.description = description
        self.context = context
        self.period = period
        self.segments = segments
        self.item = item
        self.factor = factor

    @staticmethod
    def load(cfg, comps, context, data):

        id = cfg.get("id")
        description = cfg.get("description", "?")
        segs = cfg.get("segments", {})

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        factor = float(cfg.get("factor"))

        item = comps[cfg.get("input")]

        return FactorOperation(id, description, context, pid, segs, item,
                               factor)

    def compute(self, accounts, start, end, result):

        if self.period == AT_START:
            context = self.context.with_instant(start)
        elif self.period == AT_END:
            context = self.context.with_instant(start)
        else:
            context = self.context.with_period(Period("", start, end))

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        val = self.item.compute(accounts, start, end, result)
        val = val * self.factor

        result.set(self.id, context.create_money_datum(self.id, val))
        return val

    def get_output(self, result):

        output = Total(self, self.description, result.get(self.id),
                       items=[])

        return output

class Result:
    def __init__(self):
        self.values = {}

    def set(self, id, value):
        self.values[id] = value

    def get(self, id):
        return self.values[id]

class Sum(Computable):
    def __init__(self, id, description, context, period, segments={}):
        self.id = id
        self.description = description
        self.steps = []
        self.context = context
        self.period = period
        self.segments = segments

    @staticmethod
    def load(cfg, comps, context, data):

        id = cfg.get("id", None, mandatory=False)
        if id == None: id = create_uuid()

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        segs = cfg.get("segments", {})

        comp = Sum(id, cfg.get("description", "?"), context, pid, segs)

        for item in cfg.get("inputs"):
            comp.add(get_computation(item, comps, context, data))

        return comp

    def add(self, item):
        self.steps.append(item)

    def compute(self, accounts, start, end, result):

        total = 0

        for v in self.steps:
            total += v.compute(accounts, start, end, result)

        if self.period == AT_START:
            context = self.context.with_instant(start)
        elif self.period == AT_END:
            context = self.context.with_instant(start)
        else:
            context = self.context.with_period(Period("", start, end))

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        result.set(self.id, context.create_money_datum(self.id, total))

        return total

    def get_output(self, result):

        if len(self.steps) == 0:
            
            output = NilValue(self, self.description, result.get(self.id))
            return output

        output = Total(self, self.description, result.get(self.id),
                       items=self.steps)

        return output

def get_computations(cfg, context, data):

    comp_defs = cfg.get("computations")

    comps = {}
    for comp_def in comp_defs:
        comp =  Computable.load(comp_def, comps, context, data)
        comps[comp.id] = comp
    
    return comps
