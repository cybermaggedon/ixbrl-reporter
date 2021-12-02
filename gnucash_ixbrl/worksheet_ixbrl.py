
# Converts a worksheet into iXBRL.

from . format import NegativeParenFormatter
from datetime import datetime, date
from lxml import objectify

class WorksheetIxbrl:

    def __init__(self, hide_notes):
        self.hide_notes = hide_notes

    def add_empty_row(self, table):

        row = self.par.xhtml_maker.tr({"class": "row"})
        table.append(row)

        blank = self.create_cell("\u00a0")
        blank.set("class", "label cell")
        row.append(blank)

    def create_table(self):
        grid = self.par.xhtml_maker.table()
        grid.set("class", "sheet table")
        return grid

    def add_row(self, table, elts):
        row = self.par.xhtml_maker.tr({"class": "row"})
        for elt in elts:
            row.append(elt)
        table.append(row)

    def create_cell(self, text=None):
        if text == None:
            return self.par.xhtml_maker.td()
        else:
            return self.par.xhtml_maker.td(text)

    def fmt(self, v):
        v = round(v, self.decimals)
        v = v / (10 ** self.scale)
        if self.decimals > 0:
            fmt = "{0:,.%df}" % self.decimals
        else:
            fmt = "{0:,.0f}"
        return fmt.format(v)

    def get_elt(self, worksheet, par, taxonomy, data):

        self.par = par
        self.taxonomy = taxonomy
        self.data = data

        self.decimals = self.data.get_config("metadata.accounting.decimals", 2)
        self.scale = self.data.get_config("metadata.accounting.scale", 0)
        self.currency = self.data.get_config(
            "metadata.accounting.currency", "EUR"
        )
        self.currency_label = self.data.get_config(
            "metadata.accounting.currency-label", "€"
        )
        self.tiny = (10 ** -self.decimals) / 2

        return self.create_report(worksheet)

    def add_header(self, table, periods):

        row = []

        # Blank header cell
        blank = self.create_cell("\u00a0")
        blank.set("class", "label cell")
        row.append(blank)

        if not self.hide_notes:
            # Blank note cell
            blank = self.create_cell("\u00a0")
            blank.set("class", "note cell")
            row.append(blank)

        # Header cells for period names
        for period in periods:

            elt = self.create_cell(period.name)
            row.append(elt)
            elt.set("class", "period periodname cell")

        self.add_row(table, row)

        row = []

        # Blank header cell
        blank = self.create_cell("\u00a0")
        blank.set("class", "label cell")
        row.append(blank)

        if not self.hide_notes:
            # Blank note cell
            blank = self.create_cell("\u00a0note")
            blank.set("class", "note header cell")
            row.append(blank)

        # Header cells for currencies
        for period in periods:

            elt = self.create_cell(self.currency_label)
            row.append(elt)
            elt.set("class", "period currency cell")

        self.add_row(table, row)

        # Empty row
        self.add_empty_row(table)

    def maybe_tag(self, datum, section, pid):

        fact = self.taxonomy.create_fact(datum)
        val = fact.value

        if fact.name:

            name = fact.name
            context = fact.context

            txt = self.fmt(abs(val))

            # Element always contains positive value.  For negative we
            # add parentheses
            elt = self.par.ix_maker.nonFraction(txt)
            elt.set("name", name)

            elt.set("contextRef", context)
            elt.set("format", "ixt2:numdotdecimal")
            elt.set("unitRef", self.currency)
            elt.set("decimals", str(self.decimals))
            elt.set("scale", str(self.scale))

            if abs(val) < self.tiny: val = 0

            if abs(val) < self.tiny:
                sign = False
            else:
                if val < 0:
                    sign = True
                else:
                    sign = False

                if fact.reverse:
                    sign = not sign

            if sign:
                elt.set("sign", "-")

            # Sign and negativity of value is not the same.
            # FIXME: Can't remember what the above comment means.

            if val < 0:

                span = self.par.xhtml_maker.span()
                span.append(self.par.xhtml_maker.span("( "))
                span.append(elt)
                span.append(self.par.xhtml_maker.span(" )"))
                return span

            return elt

        if abs(val) < self.tiny: val = 0

        # Sign and negativity of value is not the same.
        if val < 0:

            txt = self.fmt(-val)

            span = self.par.xhtml_maker.span()
            span.append(self.par.xhtml_maker.span("( "))
            span.append(self.par.xhtml_maker.span(txt))
            span.append(self.par.xhtml_maker.span(" )"))
            return span

        return self.par.xhtml_maker.span(self.fmt(val))

    def add_nil_section(self, table, section, periods):

        row = []

        div = self.create_cell()
        div.set("class", "label header cell")

        if len(section.total.values) > 0 and section.total.values[0].id:
            desc = self.taxonomy.create_description_fact(
                section.total.values[0], section.metadata.description
            )
            div.append(desc.to_elt(self.par))
        else:
            div.append(self.par.xhtml_maker.span(section.metadata.description))

        row.append(div)

        if not self.hide_notes:
            # note cell
            
            note = "\u00a0"

            if section.metadata.note:
                try:
                    note = self.data.get_note(section.metadata.note)
                    
                except Exception as e:
                    pass

            note = self.create_cell(note)
            note.set("class", "note cell")
            row.append(note)

        for i in range(0, len(periods)):
            div = self.create_cell()
            div.set(
                "class",
                "period total value nil rank%d cell" % section.total.rank
            )
            row.append(div)
            content = self.maybe_tag(0, section, i)
            div.append(content)

        self.add_row(table, row)

        # Empty row
        self.add_empty_row(table)

    def add_total_section(self, table, section, periods):

        row = []

        div = self.create_cell()
        div.set("class", "label header total cell")

        if len(section.total.values) > 0 and section.total.values[0].id:
            desc = self.taxonomy.create_description_fact(
                section.total.values[0], section.metadata.description
            )
            div.append(desc.to_elt(self.par))
        else:
            div.append(self.par.xhtml_maker.span(section.metadata.description))

        row.append(div)

        if not self.hide_notes:
            # note cell
            
            note = "\u00a0"

            if section.metadata.note:
                try:
                    note = self.data.get_note(section.metadata.note)
                    
                except Exception as e:
                    pass

            note = self.create_cell(note)
            note.set("class", "note cell")
            row.append(note)

        for i in range(0, len(periods)):
            div = self.create_cell()
            row.append(div)
            value = section.total.values[i]
            if abs(value.value) < self.tiny:
                div.set(
                    "class",
                    "period total value nil rank%d cell" % section.total.rank
                )
            elif value.value < 0:
                div.set(
                    "class",
                    "period total value negative rank%d cell" % section.total.rank
                )
            else:
                div.set(
                    "class",
                    "period total value rank%d cell" % section.total.rank
                )
            content = self.maybe_tag(value, section, i)
            div.append(content)

        self.add_row(table, row)

        # Empty row
        self.add_empty_row(table)

    def add_breakdown_section(self, table, section, periods):

        row = []

        div = self.create_cell()
        div.set("class", "label breakdown header cell")

        if len(section.total.values) > 0 and section.total.values[0].id:
            desc = self.taxonomy.create_description_fact(
                section.total.values[0], section.metadata.description
            )
            div.append(desc.to_elt(self.par))
        else:
            div.append(self.par.xhtml_maker.span(section.metadata.description))
        row.append(div)

        if not self.hide_notes:
            # note cell
            blank = self.create_cell("\u00a0")
            blank.set("class", "note cell")
            row.append(blank)

        self.add_row(table, row)

        for item in section.items:

            row = []

            div = self.create_cell()
            div.set("class", "label breakdown item cell")

            if len(item.values) > 0 and item.values[0].id:
                desc = self.taxonomy.create_description_fact(
                    item.values[0], item.metadata.description
                )
                div.append(desc.to_elt(self.par))
            else:
                div.append(self.par.xhtml_maker.span(item.metadata.description))

            row.append(div)

            if not self.hide_notes:
                # note cell

                note = "\u00a0"

                if item.metadata.note:
                    try:
                        note = self.data.get_note(item.metadata.note)

                    except Exception as e:
                        pass

                note = self.create_cell(note)
                note.set("class", "note cell")
                row.append(note)

            for i in range(0, len(periods)):

                value = item.values[i]

                div = self.create_cell()
                if abs(value.value) < self.tiny:
                    div.set("class",
                            "period value nil rank%d cell" % item.rank )
                elif value.value < 0:
                    div.set("class",
                            "period value negative rank%d cell" % item.rank)
                else:
                    div.set("class",
                            "period value rank%d cell" % item.rank)

                content = self.maybe_tag(value, item, i)

                div.append(content)
                row.append(div)

            self.add_row(table, row)

        row = []

        div = self.create_cell()
        div.set("class", "label breakdown total cell")
        row.append(div)
        div.append(self.par.xhtml_maker.span("Total"))

        if not self.hide_notes:
            # note cell
            
            note = "\u00a0"

            if section.metadata.note:
                try:
                    note = self.data.get_note(section.metadata.note)
                    
                except Exception as e:
                    pass

            note = self.create_cell(note)
            note.set("class", "note cell")
            row.append(note)

        for i in range(0, len(periods)):

            div = self.create_cell()

            row.append(div)

            value = section.total.values[i]

            if abs(value.value) < self.tiny:
                div.set("class",
                        "period value nil breakdown total rank%d cell" % section.total.rank)
            elif value.value < 0:
                div.set("class",
                        "period value negative breakdown total rank%d cell" % section.total.rank)
            else:
                div.set("class",
                        "period value breakdown total rank%d cell" % section.total.rank)

            content = self.maybe_tag(value, section, i)
            div.append(content)

        self.add_row(table, row)

        # Empty row
        self.add_empty_row(table)

    def add_section(self, grid, section, periods):

        if section.total == None and section.items == None:

            self.add_nil_section(grid, section, periods)

        elif section.items == None:

            self.add_total_section(grid, section, periods)

        else:

            self.add_breakdown_section(grid, section, periods)

    def create_report(self, worksheet):

        ds = worksheet.get_dataset()

        # Hide notes if the option is set, or there are no notes.
        self.hide_notes = self.hide_notes or not ds.has_notes()

        periods = ds.periods
        sections = ds.sections

        grid = self.create_table()

        self.add_header(grid, periods)

        for section in sections:
            self.add_section(grid, section, periods)

        return grid
