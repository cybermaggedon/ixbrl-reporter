
# A worksheet with a bunch of computations shown.

from . period import Period
from . worksheet import Worksheet
from . worksheet_structure import (
    Dataset, Series, Heading, Item, Totals, Break, SingleLine
)

class WorksheetSection:
    def __init__(self, id, rank=0, total_rank=0, hide_total=False):
        self.id = id
        self.rank = rank
        self.total_rank = total_rank
        self.hide_total = hide_total

class SimpleWorksheet(Worksheet):

    def __init__(self, comps, periods, data):
        self.computations = comps
        self.periods = periods
        self.data = data

    @staticmethod
    def load(defn, data):

        periods = data.get_periods()

        comps = defn.get("computations")

        ws_elts = []

        for comp in comps:
            if isinstance(comp, str):
                ws_elts.append(WorksheetSection(comp))
            else:
                ws_elts.append(WorksheetSection(
                    comp.get("id"),
                    rank=comp.get("rank", 0),
                    total_rank=comp.get("total-rank", 0),
                    hide_total=comp.get("hide-total", False)
                ))

        mpr = SimpleWorksheet(ws_elts, periods, data)

        return mpr

    def get_structure(self):

        ds = Dataset(self.periods, [])

        computations = {
            v.id: self.data.get_computation(v.id)
            for v in self.computations
        }

        results = [
            self.data.perform_computations(period)
            for period in self.periods
        ]

        if len(results) < 1:
            raise RuntimeError("No periods in worksheet?")


        for cix in range(0, len(self.computations)):

            comp_def = self.computations[cix]
            cid = comp_def.id
            computation = computations[cid]

            if computation.is_single_line():

                sec = computation.to_single_line(results)
                ds.sections.append(sec)

            else:

                sec = computation.to_heading()
                ds.sections.append(sec)

                for item in computation.to_items(results):
                    ds.sections.append(item)

                sec = Totals(computation, results)
                ds.sections.append(sec)

            ds.sections.append(Break())

        return ds
