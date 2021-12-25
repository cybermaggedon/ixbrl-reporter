
from . format import NegativeParenFormatter
from . period import Period
from . table import Row, TotalIndex
import io

class TextReporter:

    def format_number(self, n):
        if abs(n.value) < 0.001:
            return "- "
        return self.fmt.format("{0:.2f}", n.value)

    def handle_table(self, t, out):

        self.handle_header(t, out)
        self.handle_body(t, out)

    def handle_header(self, t, out):

        for lvl in range(0, t.header_levels()):

            cols = []

            def doit(col, l):
                if l == lvl:
                    cols.append((col, col.column_count()))

            t.column_recurse(doit)

            out.write(" " * self.label_width)
            for col, span in cols:

                # 1 for a space
                width = self.col_width * span - 1

                txt = col.metadata.description[:width]

                lpad = int((width - len(txt)) / 2)
                rpad = width - len(txt) - lpad

                out.write(" " * lpad)
                out.write(txt)
                out.write(" " * rpad)

                out.write(" ")

            out.write("\n")

            out.write(" " * self.label_width)
            for col, span in cols:

                # 1 for a space
                width = self.col_width * span - 1

                out.write("-" * width)

                out.write(" ")

            out.write("\n")

        # Separate from table body
        out.write("\n")

    def handle_body(self, t, out):

        def doit(x, level=0):

            if isinstance(x.child, Row):
                width = self.label_width - 1
                if isinstance(x, TotalIndex):
                    txt = "Total"
                else:
                    txt = x.metadata.description[:width]
                pad = width - len(txt)
                out.write(txt)
                out.write(" " * pad)
                out.write(":")

                for cell in x.child.values:
                    width = self.col_width - 2
                    fmt = "{0:>%d} " % width
                    n = self.format_number(cell.value)
                    txt = self.fmt.format(fmt, n)
                    out.write(txt)
                    out.write(" ")

                out.write("\n")
            else:
                width = self.label_width - 1
                txt = x.metadata.description[:width]
                pad = width - len(txt)
                out.write(txt)
                out.write(" " * pad)
                out.write("\n")
                for ix in x.child:
                    doit(ix, level + 1)
                out.write("\n")

        for ix in t.ixs:
            doit(ix)

    def output(self, worksheet, out, taxonomy):

        self.out = out
        self.fmt = NegativeParenFormatter()

        ds = worksheet.get_table(taxonomy)

        self.cols = ds.column_count()
        self.width = 80
        self.label_width = 35
        self.col_width = int((self.width - self.label_width) / self.cols)

        self.handle_table(ds, out)
