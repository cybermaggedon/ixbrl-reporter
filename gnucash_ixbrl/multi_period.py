
# A worksheet with multiple periods.


# Dataset
#   Section
#     Series

from . period import Period
from . computation import Result
from . worksheet_model import Worksheet, SimpleValue, Breakdown, NilValue, Total
from . dataset import Dataset, Section, Series

class WorksheetSection:
    def __init__(self, id, rank=0, total_rank=0, hide_total=False):
        self.id = id
        self.rank = rank
        self.total_rank = total_rank
        self.hide_total = hide_total

class MultiPeriodWorksheet(Worksheet):

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

        mpr = MultiPeriodWorksheet(ws_elts, periods, data)

        return mpr

    def get_dataset(self):

        ds = Dataset()
        ds.periods = self.periods
        ds.sections = []

        computations = {
            v.id: self.data.get_computation(v.id)
            for v in self.computations
        }

        results = [
            self.data.perform_computations(period)
            for period in self.periods
        ]

        results = [
            {
                cid: computations[cid].get_output(results[i])
                for cid in computations
            }
            for i in range(0, len(self.periods))
        ]

        for cix in range(0, len(self.computations)):

            comp_def = self.computations[cix]
            cid = comp_def.id
            computation = computations[cid]

            sec = Section()

            if len(results) < 1:
                raise RuntimeError("No periods in worksheet?")

            sec.add_data(computation, comp_def, results)

            ds.sections.append(sec)

        return ds
