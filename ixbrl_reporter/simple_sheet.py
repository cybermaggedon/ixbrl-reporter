
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

def is_all_zero(computation, results):
    for period, result in results:
        value = computation.get_output(result).value
        if abs(value.value) > 0:
            return False
    return True

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

        if computation.metadata.suppress_zero:
            if is_all_zero(computation, results):
                return None

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

        # If the whole group is suppress-zero and all zero, skip entirely
        if computation.metadata.suppress_zero:
            if is_all_zero(computation, results):
                return None

        item_ixs = []
        for item in computation.inputs:

            # Filter out zero children that have suppress-zero
            if item.metadata.suppress_zero:
                if is_all_zero(item, results):
                    continue

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

        # If all children were suppressed, render as a single line
        # instead of a group with just a total
        if len(item_ixs) == 0:
            ix = TotalIndex(computation.metadata, Row(cells), notes=note)
            ix = Index(computation.metadata, [ix])
            return ix

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
            else:
                ix = self.get_single_line_ix(computation, results)

            if ix is not None:
                ixs.append(ix)

        tbl = Table(columns, ixs)

        return tbl

