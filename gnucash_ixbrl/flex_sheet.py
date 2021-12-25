
from . worksheet import Worksheet
from . computation import Metadata
from . table import Table, Column, Index, TotalIndex, Row, Cell

class WorksheetSection:
    def __init__(self, comp, kind, rank=0, total_rank=0, hide_total=False):
        self.comp = comp
        self.kind = kind
        self.rank = rank
        self.total_rank = total_rank
        self.hide_total = hide_total

class FlexWorksheet(Worksheet):

    def __init__(self, columns, indexes, periods, data):
        self.columns = columns
        self.indexes = indexes
        self.periods = periods
        self.data = data

    @staticmethod
    def load(defn, data):

        columns = defn.get("columns")
        indexes = defn.get("indexes")
        periods = data.get_periods()

        return FlexWorksheet(columns, indexes, periods, data)

    def get_columns(self, cols):

        ret = []

        for col in cols:

            label = str(col.get("label"))
            unit_label = col.get("units", mandatory=False)

            m = Metadata(None, label, None, {}, None, None)
            
            subcols = col.get("columns", mandatory=False)
            if subcols:
                child = self.get_columns(subcols)
            else:
                child = None

            if unit_label:
                col = Column(m, child, unit_label)
            else:
                col = Column(m, child)
            ret.append(col)


        return ret

    def get_row(self, row):

        cells = []

        for elt in row:

            if elt.get("context", mandatory=False):
                context = self.taxonomy.get_context(elt.get("context"))
            else:
                context = self.context

            datum = self.data.to_datum(elt, context)
            
            cells.append(Cell(datum))
                
        return Row(cells)

    def get_indexes(self, ixs):

        ret = []

        for ix in ixs:

            id = ix.get("id")
            desc = ix.get("description")

            m = Metadata(id, desc, None, {}, None, None)
            
            subixs = ix.get("indexes", mandatory=False)
            if subixs:
                child = self.get_indexes(subixs)
                ret.append(Index(m, child))
                continue

            row = ix.get("row", mandatory=False)
            if row:
                child = self.get_row(row)
                ret.append(Index(m, child))
                continue
            
            row = ix.get("total", mandatory=False)
            if row:
                child = self.get_row(row)
                ret.append(TotalIndex(m, child))
                continue

            raise RuntimeError("Could not make sense of index definition")

        return ret

    def get_table(self, taxonomy):

        self.taxonomy = taxonomy

        self.currency_label = self.data.get_config(
            "metadata.accounting.currency-label", "€"
        )

        period = self.data.get_report_period()
        self.context = self.data.get_business_context().with_period(period)

        cols = self.get_columns(self.columns)
        ixs = self.get_indexes(self.indexes)

        ds = Table(cols, ixs)

        return ds
