
# Computations used to compute values from GnuCash accounts.
import json
import datetime
import uuid

from . result import SimpleResult, BreakdownResult, NilResult, TotalResult
from . period import Period

def get_computation(item, comps, context, data, gcfg):
    if isinstance(item, str):
        return comps[item]
    return Computable.load(item, comps, context, data, gcfg)

def create_uuid():
    return str(uuid.uuid4())

IN_YEAR = 1
AT_START = 2
AT_END = 3

ROUND_DOWN = 1
ROUND_UP = 2
ROUND_NEAREST = 3

CMP_LESS = 1
CMP_LESS_EQUAL = 2
CMP_GREATER = 3
CMP_GREATER_EQUAL = 4

class Metadata:
    def __init__(self, id, description, context, segments, period, note):
        self.id = id
        self.description = description
        self.context = context
        self.segments = segments
        self.period = period
        self.note = note
        
    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        id = cfg.get("id", None, mandatory=False)
        if id == None: id = create_uuid()

        pspec = cfg.get("period", "at-end")

        pid = {
            "in-year": IN_YEAR,
            "at-start": AT_START,
            "at-end": AT_END
        }.get(pspec, AT_END)

        segsdef = cfg.get("segments", [])
        if not isinstance(segsdef, list):
            raise RuntimeError(
                "segments should be list of single-item maps"
            )

        segs = []

        for elt in segsdef:
            if len(elt) != 1:
                raise RuntimeError(
                    "segments should be list of single-item maps"
                )
            # Will loop only once
            for k, v in elt.items():
                segs.append((k, gcfg.get(v, v)))

        description = cfg.get("description", "?")
        note = cfg.get("note", mandatory=False)

        if note: note = str(note)

        return Metadata(id, description, context, segs, pid, note)

    def get_context(self, start, end):

        if self.period == AT_START:
            context = self.context.with_instant(start)
        elif self.period == AT_END:
            context = self.context.with_instant(end)
        else: # IN_YEAR
            context = self.context.with_period(Period("", start, end))

        if len(self.segments) != 0:
            context = context.with_segments(self.segments)

        return context

    def result(self, result):
        return result.get(self.id)
        
class Computable:
    def compute(self, accounts, start, end, result):
        raise RuntimeError("Not implemented")

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        kind = cfg.get("kind")

        if kind == "group":
            return Group.load(cfg, comps, context, data, gcfg)

        if kind == "sum":
            return Sum.load(cfg, comps, context, data, gcfg)

        if kind == "abs":
            return AbsOperation.load(cfg, comps, context, data, gcfg)

        if kind == "apportion":
            return ApportionOperation.load(cfg, comps, context, data, gcfg)

        # For UK corporation tax.  >:-O
        if kind == "round":
            return RoundOperation.load(cfg, comps, context, data, gcfg)

        if kind == "factor":
            return FactorOperation.load(cfg, comps, context, data, gcfg)

        if kind == "compare":
            return Comparison.load(cfg, comps, context, data, gcfg)

        if kind == "line":
            return Line.load(cfg, comps, context, data, gcfg)

        if kind == "constant":
            return Constant.load(cfg, comps, context, data, gcfg)

        raise RuntimeError("Don't understand computable type '%s'" % kind)

class Line(Computable):

    def __init__(self, metadata, accounts, reverse=False):
        self.metadata = metadata
        self.accounts = accounts
        self.reverse = reverse

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)

        return Line(
            metadata, cfg.get("accounts"), cfg.get_bool("reverse-sign", False)
        )

    def compute(self, session, start, end, result):

        total = 0

        # FIXME: If there are transactions preceding 1970, this won't work.
        if self.metadata.period == AT_START:
            context = self.metadata.context.with_instant(start)
            history = datetime.date(1970, 1, 1)
            start, end = history, start
        elif self.metadata.period == AT_END:
            context = self.metadata.context.with_instant(end)
            history = datetime.date(1970, 1, 1)
            start, end = history, end
        else: # IN_YEAR
            context = self.metadata.context.with_period(Period("", start, end))
            
        for acct_name in self.accounts:
            acct = session.get_account(None, acct_name)

            splits = session.get_splits(acct, start, end)

            acct_total = sum([v["amount"] for v in splits])

            if session.is_debit(acct):
                acct_total *= -1

            total += acct_total

        if self.reverse: total *= -1

        if len(self.metadata.segments) != 0:
            context = context.with_segments(self.metadata.segments)

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, total)
        )

        return total

    def get_output(self, result):

        if len(self.accounts) == 0:
            output = NilResult(self, self.metadata.result(result)
            )
            return output

        output = TotalResult(self, self.metadata.result(result), items=[])

        return output

class Constant(Computable):
    def __init__(self, metadata, values):
        self.metadata = metadata
        self.values = values

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)
        return Constant(metadata, cfg.get("values"))

    def compute(self, session, start, end, result):

        context = self.metadata.get_context(start, end)
        val = self.values[str(end)]

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, val)
        )

        return val

    def get_output(self, result):

        output = SimpleValue(
            self,
            result.get(self.metadata.id)
        )

        return output

class Group(Computable):
    def __init__(self, metadata, inputs=None):

        if inputs == None:
            inputs = []

        self.metadata = metadata
        self.inputs = inputs

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)
        comp = Group(metadata, [])

        for item in cfg.get("inputs"):
            comp.add(get_computation(item, comps, context, data, gcfg))

        def set_hide(x):
            comp.hide_breakdown = x

        cfg.get("hide-breakdown", False).use(set_hide)
        
        return comp

    def is_single_line(self):
        if len(self.inputs) == 0:
            return True
        else:
            return False

    def add(self, input):
        self.inputs.append(input)

    def compute(self, accounts, start, end, result):

        context = self.metadata.get_context(start, end)

        total = 0
        for input in self.inputs:
            total += input.compute(accounts, start, end, result)

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, total)
        )

        return total

    def get_output(self, result):

        if len(self.inputs) == 0:
            output = NilResult(self, result.get(self.metadata.id))
            return output

        if self.hide_breakdown:

            # For a hidden breakdown, create a breakdown object which is not
            # returned, and a Total object which references it
            bd = BreakdownResult(
                self,
                result.get(self.metadata.id),
                items=[
                    item.get_output(result) for item in self.inputs
                ]
            )

            output = TotalResult(self, self.metadata, result.get(self.metadata.id),
                                 items=[bd])

        else:

            output = BreakdownResult(
                self,
                result.get(self.metadata.id),
                items= [
                    item.get_output(result) for item in self.inputs
                ]
            )

        return output

class ApportionOperation(Computable):
    def __init__(self, metadata, item, part, whole):
        self.metadata = metadata
        self.item = item
        self.fraction = part.days() / whole.days()

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)

        whole_key = cfg.get("whole-period")
        whole = Period.load(data.get_config(whole_key))
        proportion_key = cfg.get("proportion-period")
        proportion = Period.load(data.get_config(proportion_key))

        item = cfg.get("input")

        return ApportionOperation(
            metadata,
            get_computation(item, comps, context, data, gcfg),
            proportion,
            whole
        )

    def compute(self, accounts, start, end, result):

        context = self.metadata.get_context(start, end)

        val = self.item.compute(accounts, start, end, result)
        val *= self.fraction

        result.set(self.metadata.id,
                   context.create_money_datum(self.metadata.id, val)
                   )
        return val

    def get_output(self, result):

        output = TotalResult(self, result.get(self.metadata.id), items=[])

        return output

class RoundOperation(Computable):
    def __init__(self, metadata, dir, item):
        self.metadata = metadata
        self.direc = dir
        self.item = item

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)

        direc = {
            "nearest": ROUND_NEAREST,
            "down": ROUND_DOWN,
            "up": ROUND_UP
        }.get(cfg.get("direction", "nearest"), ROUND_NEAREST)

        item = cfg.get("input")

        return RoundOperation(
            metadata, direc,
            get_computation(item, comps, context, data, gcfg)
        )

    def compute(self, accounts, start, end, result):

        context = self.metadata.get_context(start, end)

        val = self.item.compute(accounts, start, end, result)

        if self.direc == ROUND_NEAREST:
            val = round(val)    # Round to nearest int
        elif self.direc == ROUND_DOWN:
            val = int(val)      # Round down
        else:
            val = int(val + 1)  # Round up

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, val)
        )
        return val

    def get_output(self, result):

        output = TotalResult(self, result.get(self.metadata.id), items=[])

        return output

class FactorOperation(Computable):
    def __init__(self, metadata, item, factor):
        self.metadata = metadata
        self.item = item
        self.factor = factor

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)
        factor = float(cfg.get("factor"))
        item = cfg.get("input")

        return FactorOperation(
            metadata,
            get_computation(item, comps, context, data, gcfg),
            factor
        )

    def compute(self, accounts, start, end, result):

        context = self.metadata.get_context(start, end)

        val = self.item.compute(accounts, start, end, result)
        val = val * self.factor

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, val)
        )
        return val

    def get_output(self, result):

        output = TotalResult(self, result.get(self.metadata.id), items=[])

        return output

class Comparison(Computable):
    def __init__(self, metadata, item, comparison, value=0, false_value=0):
        self.metadata = metadata
        self.item = item
        self.value = value
        self.false_value = false_value
        self.comparison = comparison

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)

        comparison = cfg.get("comparison")

        cid = {
            "less": CMP_LESS,
            "less-or-equal": CMP_LESS_EQUAL,
            "greater": CMP_GREATER,
            "greater-or-equal": CMP_GREATER_EQUAL,
        }.get(comparison, CMP_LESS)

        try:
            value = float(cfg.get("value"))
        except: value = 0

        try:
            if_false = float(cfg.get("if-false"))
        except: if_false = 0

        item = cfg.get("input")

        return Comparison(
            metadata,
            get_computation(item, comps, context, data, gcfg),
            cid,
            value,
            if_false
        )

    def compute(self, accounts, start, end, result):

        context = self.metadata.get_context(start, end)

        val = self.item.compute(accounts, start, end, result)

        if self.comparison == CMP_LESS and val >= self.value:
            val = self.false_value
        elif self.comparison == CMP_LESS_EQUAL and val > self.value:
            val = self.false_value
        if self.comparison == CMP_GREATER and val <= self.value:
            val = self.false_value
        if self.comparison == CMP_GREATER_EQUAL and val < self.value:
            val = self.false_value

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, val)
        )
        return val

    def get_output(self, result):

        output = TotalResult(self, result.get(self.metadata.id), items=[])

        return output

class Sum(Computable):
    def __init__(self, metadata):
        self.metadata = metadata
        self.steps = []

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)

        comp = Sum(metadata)

        for item in cfg.get("inputs"):
            comp.add(get_computation(item, comps, context, data, gcfg))

        return comp

    def add(self, item):
        self.steps.append(item)

    def compute(self, accounts, start, end, result):

        total = 0

        for v in self.steps:
            total += v.compute(accounts, start, end, result)

        context = self.metadata.get_context(start, end)

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, total)
        )

        return total

    def get_output(self, result):

        if len(self.steps) == 0:
            
            output = NilResult(self, result.get(self.metadata.id))
            return output

        output = TotalResult(self, result.get(self.metadata.id), items=self.steps)

        return output

class AbsOperation(Computable):
    def __init__(self, metadata, item):
        self.metadata = metadata
        self.item = item

    @staticmethod
    def load(cfg, comps, context, data, gcfg):

        metadata = Metadata.load(cfg, comps, context, data, gcfg)

        item = cfg.get("input")

        return AbsOperation(
            metadata, get_computation(item, comps, context, data, gcfg)
        )

    def compute(self, accounts, start, end, result):

        context = self.metadata.get_context(start, end)

        val = self.item.compute(accounts, start, end, result)

        val = abs(val)

        result.set(
            self.metadata.id,
            context.create_money_datum(self.metadata.id, val)
        )
        return val

    def get_output(self, result):

        output = TotalResult(self, result.get(self.metadata.id), items=[])

        return output

def get_computations(gcfg, context, data):

    comp_defs = gcfg.get("report.computations")

    comps = {}
    for comp_def in comp_defs:
        comp =  Computable.load(comp_def, comps, context, data, gcfg)
        comps[comp.metadata.id] = comp
    
    return comps

class ResultSet(dict):
    def set(self, id, value):
        self[id] = value
    def get(self, id):
        return self[id]

