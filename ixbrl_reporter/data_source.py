
from . period import Period
from . context import Context
from . computation import get_computations, ResultSet
from . valueset import ValueSet
from . simple_sheet import SimpleWorksheet
from . flex_sheet import FlexWorksheet
from . element import Element
from . config import NoneValue
from . datum import *
from . expand import expand_string

class NoteHeadings(dict):
    def maybe_init(self, level):
        if level not in self:
            self[level] = 1
    def get_next(self, level):

        if level == 1:
            if 2 in self:
                del self[2]

        self.maybe_init(level)
        n = self[level]
        self[level] += 1
        return n

class DataSource:
    def __init__(self, cfg, session):

        self.cfg = cfg
        self.session = session

        self.root_context = Context(None)
        self.business_context = self.root_context.with_entity(
            self.cfg.get("metadata.business.entity-scheme"),
            self.cfg.get("metadata.business.company-number")
        )
        self.computations = get_computations(cfg, self.business_context, self)
        self.results = {}

        self.notes = {}

        self.noteheadings = NoteHeadings()

    def set_note(self, id, value):
        self.notes[id] = value

    def expand_string(self, value):
        return expand_string(value, self)

    def get_note(self, id):
        return self.notes[id]

    def get_business_context(self):
        return self.business_context

    def get_root_context(self):
        return self.root_context

    def get_report_period(self, i=0):

        return Period.load(self.cfg.get("metadata.accounting.periods." + str(i)))

    def get_report_date(self):

        return self.cfg.get_date("metadata.accounting.date")

    def get_computation(self, id):
        if id in self.computations:
            return self.computations[id]
        raise RuntimeError("No such computation '%s'" % id)

    def perform_computations(self, period):

        c = self.business_context.with_period(period)

        if c not in self.results:
            res = ResultSet()
            self.results[c] = res

            for comp in self.computations.values():
                comp.compute(self.session, period.start, period.end, res)

        return self.results[c]

    def get_result(self, id, period):
        res = self.get_results([id], period)
        return res.get(id)

    def get_results(self, ids, period):

        res = self.perform_computations(period)

        d = ValueSet()
        for id in ids:
            d.add_datum(res.get(id))

        return d

    def get_periods(self):
        return [
            Period.load(period)
            for period in self.cfg.get("metadata.accounting.periods")
        ]

    def get_period(self, name):

        for period in self.get_periods():
            if period.name == name:
                return period

        raise RuntimeError("Period '" + period + "' not known")

    def get_worksheet(self, id):

        for ws_def in self.cfg.get("report.worksheets"):

            if ws_def.get("id") == id:

                kind = ws_def.get("kind")

                if kind == "simple":
                    return SimpleWorksheet.load(ws_def, self)
                if kind == "flex":
                    return FlexWorksheet.load(ws_def, self)

                raise RuntimeError("Don't know worksheet type '%s'" % kind)

        raise RuntimeError("Could not find worksheet '%s'" % id)

    def get_element(self, elt):

        # This deals with inline
        if isinstance(elt, dict):
            if "kind" in elt:
                return Element.load(elt, self)

        # This deals with references

        elt_defs = self.cfg.get("report.elements")

        for elt_def in elt_defs:
            if elt_def.get("id") == elt:
                return Element.load(elt_def, self)

        raise RuntimeError("Could not find element '%s'" % elt)

    def get_config(self, key, deflt=None, mandatory=True):
        return self.cfg.get(key, deflt, mandatory)

    def get_config_date(self, key, deflt=None, mandatory=True):
        return self.cfg.get_date(key, deflt, mandatory)

    def get_config_bool(self, key, deflt=None, mandatory=True):
        return self.cfg.get_bool(key, deflt, mandatory)

    def to_datum(self, defn, context):

        # FIXME: All datum to over-ride context? (currently happens in fact_table)

        if defn.get("kind") == "config":
            id = defn.get("id")
            value = self.get_config(defn.get("key"))
            datum = StringDatum(id, value, context)
            return datum
        elif defn.get("kind") == "config-date":
            id = defn.get("id")
            value = self.get_config_date(defn.get("key"))
            datum = DateDatum(id, value, context)
            return datum
        elif defn.get("kind") == "bool":
            id = defn.get("id")
            value = defn.get_bool("value")
            datum = BoolDatum(id, value, context)
            return datum
        elif defn.get("kind") == "string":
            id = defn.get("id")
            value = defn.get("value")
            datum = StringDatum(id, value, context)
            return datum
        elif defn.get("kind") == "money":
            id = defn.get("id")
            value = defn.get("value")
            datum = MoneyDatum(id, value, context)
            return datum
        elif defn.get("kind") == "number":
            id = defn.get("id")
            value = defn.get("value")
            datum = NumberDatum(id, value, context)
            return datum
        elif defn.get("kind") == "computation":

            comp_id = defn.get("computation")
            key = defn.get("period-config")
            period = Period.load(self.get_config(
                key
            ))
            res = self.get_results([comp_id], period)
            value = res.get(comp_id)

            return value

        elif defn.get("kind") == "variable":
            id = None
            variable = defn.get("variable")
            datum = VariableDatum(id, variable, context)
            return datum

