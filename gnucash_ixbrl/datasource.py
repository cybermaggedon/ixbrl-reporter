
from . period import Period
from . context import Context
from . computation import get_computations, Result
from . valueset import ValueSet
from . multi_period import MultiPeriodWorksheet
from . element import Element
from . config import NoneValue

class DataSource:
    def __init__(self, cfg, session):

        self.cfg = cfg
        self.session = session

        self.root_context = Context(None)
        self.business_context = self.root_context.with_entity(
            "http://www.companieshouse.gov.uk/",
            self.cfg.get("metadata.business.company-number")
        )
        self.computations = get_computations(cfg, self.business_context, self)
        self.results = {}

    def get_business_context(self):
        return self.business_context

    def get_root_context(self):
        return self.root_context

    def get_report_period(self, i=0):

        return Period.load(self.cfg.get("metadata.report.periods." + str(i)))

    def get_report_date(self):

        return self.cfg.get_date("metadata.report.date")

    def get_computation(self, id):
        if id in self.computations:
            return self.computations[id]
        raise RuntimeError("No such computation '%s'" % id)

    def perform_computations(self, period):

        c = self.business_context.with_period(period)

        if c not in self.results:
            res = Result()
            self.results[c] = res

            for comp in self.computations.values():
                comp.compute(self.session, period.start, period.end, res)

        return self.results[c]

    def get_results(self, ids, period):

        res = self.perform_computations(period)

        d = ValueSet()
        for id in ids:
            d.add_datum(res.get(id))

        return d

    def get_periods(self):
        return [
            Period.load(period)
            for period in self.cfg.get("metadata.report.periods")
        ]

    def get_worksheet(self, id):

        for ws_def in self.cfg.get("worksheets"):

            if ws_def.get("id") == id:

                kind = ws_def.get("kind")

                if kind == "multi-period":
                    return MultiPeriodWorksheet.load(ws_def, self)

                raise RuntimeError("Don't know worksheet type '%s'" % kind)

        raise RuntimeError("Could not find worksheet '%s'" % id)

    def get_element(self, id):

        elt_defs = self.cfg.get("elements")

        for elt_def in elt_defs:

            if elt_def.get("id") == id:
                return Element.load(elt_def, self)

        raise RuntimeError("Could not find element '%s'" % id)

    def get_config(self, key, deflt=None):
        return self.cfg.get(key, deflt)

    def get_config_date(self, key, deflt=None):
        return self.cfg.get_date(key, deflt)

