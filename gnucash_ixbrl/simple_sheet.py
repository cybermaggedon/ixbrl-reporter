
# A worksheet with a bunch of computations shown.

from . period import Period
from . worksheet import Worksheet
from . table import (
    Cell, Row, Index, Column, Table, TotalIndex
)
from . computation import Metadata, Group

class WorksheetSection:
    def __init__(self, id):
        self.id = id

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
                ws_elts.append(WorksheetSection(comp.get("id")))

        mpr = SimpleWorksheet(ws_elts, periods, data)

        return mpr

    def get_single_line_ix(self, computation, results):

        cells = []

        for period, result in results:
            cells.append(
                Cell(
                    computation.get_output(result).value
                )
            )

        note = None
        if computation.metadata.note:
            try:
                note = self.data.get_note(computation.metadata.note)
            except:
                pass

        ix = TotalIndex(computation.metadata, Row(cells), notes=note)
        ix = Index(computation.metadata, [ix])

        return ix

    def get_breakdown_ix(self, computation, results):

        item_ixs = []
        for item in computation.inputs:

            note = None
            if item.metadata.note:
                try:
                    note = self.data.get_note(item.metadata.note)
                except:
                    pass

            cells = []
            for period, result in results:
                cells.append(
                    Cell(
                        item.get_output(result).value
                    )
                )
            ix = Index(item.metadata, Row(cells), notes=note)
            item_ixs.append(ix)

        # Total
        cells = []
        for period, result in results:
            cells.append(
                Cell(
                    computation.get_output(result).value
                )
            )

        note = None
        if computation.metadata.note:
            try:
                note = self.data.get_note(computation.metadata.note)
            except:
                pass

        ix = TotalIndex(computation.metadata, Row(cells))
        item_ixs.append(ix)

        ix = Index(computation.metadata, item_ixs, notes=note)

        return ix

    def get_table(self, taxonomy):

        if len(self.periods) < 1:
            raise RuntimeError("No periods in worksheet?")

        computations = {
            v.id: self.data.get_computation(v.id)
            for v in self.computations
        }

        self.currency_label = self.data.get_config(
            "metadata.accounting.currency-label", "€"
        )

        results = [
            (period, self.data.perform_computations(period))
            for period in self.periods
        ]

        columns = []
        for period in self.periods:
            m = Metadata(None, period.name, None, {}, period, None)
            col = Column(m, None, self.currency_label)
            columns.append(col)

        ixs = []

        for cix in range(0, len(self.computations)):

            comp_def = self.computations[cix]
            cid = comp_def.id
            computation = computations[cid]

            if isinstance(computation, Group):

                ix = self.get_breakdown_ix(computation, results)
                ixs.append(ix)

            else:
                ixs.append(self.get_single_line_ix(computation, results))

        tbl = Table(columns, ixs)

        return tbl

