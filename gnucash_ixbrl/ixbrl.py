
# Converts a worksheet into iXBRL.

from . format import NegativeParenFormatter
from xml.dom.minidom import getDOMImplementation
from xml.dom import XHTML_NAMESPACE
from datetime import datetime, date

class IxbrlReporter:

    def get_elt(self, worksheet, par, taxonomy):

        self.doc = par.doc
        self.taxonomy = taxonomy

        return self.create_report(worksheet)

    def add_header(self, grid, periods):

        # Blank header cell
        blank = self.doc.createElement("div")
        blank.setAttribute("class", "label")
        grid.appendChild(blank)
        blank.appendChild(self.doc.createTextNode(" "))

        # Header cells for period names
        for period in periods:

            elt = self.doc.createElement("div")
            grid.appendChild(elt)
            elt.setAttribute("class", "period periodname")
            elt.appendChild(self.doc.createTextNode(period.name))

        # Blank header cell
        blank = self.doc.createElement("div")
        blank.setAttribute("class", "label")
        grid.appendChild(blank)
        blank.appendChild(self.doc.createTextNode(" "))

        # Header cells for period names
        for period in periods:

            elt = self.doc.createElement("div")
            grid.appendChild(elt)
            elt.setAttribute("class", "period currency")
            elt.appendChild(self.doc.createTextNode("£"))

    def maybe_tag(self, datum, section, pid):

        value = self.taxonomy.create_fact(datum)

        if value.name:

            name = value.name
            context = value.context

            elt = self.doc.createElement("ix:nonFraction")
            elt.setAttribute("name", name)

            elt.setAttribute("contextRef", context)
            elt.setAttribute("format", "ixt2:numdotdecimal")
            elt.setAttribute("unitRef", "GBP")
            elt.setAttribute("decimals", "2")

            val = value.value
            if abs(val) < 0.005: val = 0

            if abs(val) < 0.005:
                sign = False
            else:
                if val < 0:
                    sign = True
                else:
                    sign = False

                if value.reverse:
                    sign = not sign

            if sign:
                elt.setAttribute("sign", "-")

            # Sign and negativity of value is not the same.

            if val < 0:

                txt = self.doc.createTextNode("{0:,.2f}".format(-val))
                elt.appendChild(txt)

                span = self.doc.createElement("span")
                span.appendChild(self.doc.createTextNode("( "))
                span.appendChild(elt)
                span.appendChild(self.doc.createTextNode(" )"))
                return span

            txt = self.doc.createTextNode("{0:,.2f}".format(val))
            elt.appendChild(txt)

            return elt

        val = value.value
        if abs(val) < 0.005: val = 0

        # Sign and negativity of value is not the same.
        if val < 0:

            txt = self.doc.createTextNode("{0:,.2f}".format(-val))

            span = self.doc.createElement("span")
            span.appendChild(self.doc.createTextNode("( "))
            span.appendChild(txt)
            span.appendChild(self.doc.createTextNode(" )"))
            return span

        txt = self.doc.createTextNode("{0:,.2f}".format(val))
        return txt

    def add_nil_section(self, grid, section, periods):

        div = self.doc.createElement("div")
        div.setAttribute("class", "label header")

        if len(section.total.values) > 0 and section.total.values[0].id:
            desc = self.taxonomy.create_description_fact(
                section.total.values[0], section.header
            )
            desc.append(self.doc, div)
        else:
            div.appendChild(self.doc.createTextNode(section.header))

        grid.appendChild(div)

        for i in range(0, len(periods)):
            div = self.doc.createElement("div")
            div.setAttribute(
                "class",
                "period total value nil rank%d" % section.total.rank
            )
            grid.appendChild(div)
            content = self.maybe_tag(0, section, i)
            div.appendChild(content)

    def add_total_section(self, grid, section, periods):

        div = self.doc.createElement("div")
        div.setAttribute("class", "label header total")

        if len(section.total.values) > 0 and section.total.values[0].id:
            desc = self.taxonomy.create_description_fact(
                section.total.values[0], section.header
            )
            desc.append(self.doc, div)
        else:
            div.appendChild(self.doc.createTextNode(section.header))

        grid.appendChild(div)

        for i in range(0, len(periods)):
            div = self.doc.createElement("div")
            grid.appendChild(div)
            value = section.total.values[i]
            if abs(value.value) < 0.001:
                div.setAttribute(
                    "class",
                    "period total value nil rank%d" % section.total.rank
                )
            elif value.value < 0:
                div.setAttribute(
                    "class",
                    "period total value negative rank%d" % section.total.rank
                )
            else:
                div.setAttribute(
                    "class",
                    "period total value rank%d" % section.total.rank
                )
            content = self.maybe_tag(value, section, i)
            div.appendChild(content)

    def add_breakdown_section(self, grid, section, periods):

        div = self.doc.createElement("div")
        div.setAttribute("class", "label breakdown header")

        if len(section.total.values) > 0 and section.total.values[0].id:
            desc = self.taxonomy.create_description_fact(
                section.total.values[0], section.header
            )
            desc.append(self.doc, div)
        else:
            div.appendChild(self.doc.createTextNode(section.header))
        grid.appendChild(div)

        for item in section.items:

            div = self.doc.createElement("div")
            div.setAttribute("class", "label breakdown item")

            if len(item.values) > 0 and item.values[0].id:
                desc = self.taxonomy.create_description_fact(
                    item.values[0], item.description
                )
                desc.append(self.doc, div)
            else:
                div.appendChild(self.doc.createTextNode(item.description))

            grid.appendChild(div)

            for i in range(0, len(periods)):

                value = item.values[i]

                div = self.doc.createElement("div")
                if abs(value.value) < 0.001:
                    div.setAttribute("class",
                                     "period value nil rank%d" % item.rank )
                elif value.value < 0:
                    div.setAttribute("class",
                                     "period value negative rank%d" % item.rank)
                else:
                    div.setAttribute("class",
                                     "period value rank%d" % item.rank)

                content = self.maybe_tag(value, item, i)

                div.appendChild(content)
                grid.appendChild(div)

        div = self.doc.createElement("div")
        div.setAttribute("class", "label breakdown total")
        grid.appendChild(div)
        div.appendChild(self.doc.createTextNode("Total"))

        for i in range(0, len(periods)):

            div = self.doc.createElement("div")

            grid.appendChild(div)

            value = section.total.values[i]

            if abs(value.value) < 0.001:
                div.setAttribute("class",
                                 "period value nil breakdown total rank%d" % section.total.rank)
            elif value.value < 0:
                div.setAttribute("class",
                                 "period value negative breakdown total rank%d" % section.total.rank)
            else:
                div.setAttribute("class", "period value breakdown total rank%d" % section.total.rank)

            content = self.maybe_tag(value, section, i)
            div.appendChild(content)

    def add_section(self, grid, section, periods):

        if section.total == None and section.items == None:

            self.add_nil_section(grid, section, periods)

        elif section.items == None:

            self.add_total_section(grid, section, periods)

        else:

            self.add_breakdown_section(grid, section, periods)

    def create_report(self, worksheet):

        ds = worksheet.get_dataset()
        periods = ds.periods
        sections = ds.sections

        grid = self.doc.createElement("div")
        grid.setAttribute("class", "sheet")

        self.add_header(grid, periods)

        for section in sections:

            self.add_section(grid, section, periods)

        return grid

