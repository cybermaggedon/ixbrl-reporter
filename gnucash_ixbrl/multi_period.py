
# A worksheet with multiple periods.

from . period import Period
from . computation import Result
from . worksheet_model import Worksheet, SimpleValue, Breakdown, NilValue, Total
from . fact import *

class WorksheetElement:
    def __init__(self, id, rank=0, total_rank=0):
        self.id = id
        self.rank = rank
        self.total_rank = total_rank

class MultiPeriodWorksheet(Worksheet):

    def __init__(self, comps, periods):
        self.computations = comps
        self.periods = periods

    @staticmethod
    def load(defn, data):

        periods = data.get_periods()

        comps = defn.get("computations")

        ws_elts = []

        for comp in comps:
            if isinstance(comp, str):
                ws_elts.append(WorksheetElement(comp))
            else:
                ws_elts.append(WorksheetElement(
                    comp.get("id"),
                    rank=comp.get("rank", 0),
                    total_rank=comp.get("total-rank", 0)
                ))

        mpr = MultiPeriodWorksheet(ws_elts, periods)

        mpr.process(data)

        return mpr

    def process(self, data):

        self.inputs = [
            data.get_computation(v.id)
            for v in self.computations
        ]
        self.outputs = {}

        for period in self.periods:

            res = data.perform_computations(period)

            period_output = {}

            for input in self.inputs:

                period_output[input.id] = input.get_output(res)

            self.outputs[period] = period_output

    def get_dataset(self):

        ds = Dataset()
        ds.periods = [v for v in self.periods]
        ds.sections = []

        elts = {
            v.id: v
            for v in self.computations
        }

        for input in self.inputs:

            output0 = self.outputs[self.periods[0]][input.id]

            if isinstance(output0, Breakdown):

                sec = Section()
                sec.id = input.id
                sec.header = input.description
                sec.total = Series("Total", [
                    self.outputs[period][input.id].value
                    for period in self.periods
                ], rank=elts[input.id].total_rank)

                items = []
                for i in range(0, len(output0.items)):
                    srs  = Series(
                        output0.items[i].description,
                        [
                            self.outputs[period][input.id].items[i].value
                            for period in self.periods
                        ],
                        rank=elts[input.id].rank
                    )
                    srs.id = output0.defn.inputs[i].id
                    items.append(srs)
                sec.items = items

                ds.sections.append(sec)

            elif isinstance(output0, NilValue):

                sec = Section()
                sec.id = input.id
                sec.header = input.description
                sec.items = None
                sec.total = Series("Total", [
                    self.outputs[period][input.id].value
                    for period in self.periods
                ], rank=elts[input.id].total_rank)
                ds.sections.append(sec)

            elif isinstance(output0, Total):

                sec = Section()
                sec.id = input.id
                sec.header = input.description
                sec.items = None
                sec.total = Series("Total", [
                    self.outputs[period][input.id].value
                    for period in self.periods
                ], rank=elts[input.id].total_rank)
                ds.sections.append(sec)

        return ds
