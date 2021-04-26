
# Converts a worksheet into iXBRL.

from . format import NegativeParenFormatter
from xml.dom.minidom import getDOMImplementation
from xml.dom import XHTML_NAMESPACE
from datetime import datetime, date

class IxbrlReporter:

    def get_elt(self, worksheet, par, taxonomy):

        fmt = NegativeParenFormatter()

        def format_number(n):
            return fmt.format("{0:,.2f}", n)

        doc = par.doc

        def add_header(grid, periods):

            # Blank header cell
            blank = doc.createElement("div")
            blank.setAttribute("class", "label")
            grid.appendChild(blank)
            blank.appendChild(doc.createTextNode(" "))

            # Header cells for period names
            for period in periods:

                elt = doc.createElement("div")
                grid.appendChild(elt)
                elt.setAttribute("class", "period periodname")
                elt.appendChild(doc.createTextNode(period.name))

            # Blank header cell
            blank = doc.createElement("div")
            blank.setAttribute("class", "label")
            grid.appendChild(blank)
            blank.appendChild(doc.createTextNode(" "))

            # Header cells for period names
            for period in periods:

                elt = doc.createElement("div")
                grid.appendChild(elt)
                elt.setAttribute("class", "period currency")
                elt.appendChild(doc.createTextNode("£"))

        def maybe_tag(datum, section, pid):

            value = taxonomy.create_fact(datum)

            if value.name:

                name = value.name
                context = value.context

                elt = doc.createElement("ix:nonFraction")
                elt.setAttribute("name", name)

                elt.setAttribute("contextRef", context)
                elt.setAttribute("format", "ixt2:numdotdecimal")
                elt.setAttribute("unitRef", "GBP")
                elt.setAttribute("decimals", "2")

                if abs(value.value) < 0.001:
                    sign = False
                else:
                    if value.value < 0:
                        sign = True
                    else:
                        sign = False

                    if value.reverse:
                        sign = not sign

                if sign:
                    elt.setAttribute("sign", "-")

                # Sign and negativity of value is not the same.

                if value.value < 0:

                    txt = doc.createTextNode("{0:,.2f}".format(-value.value))
                    elt.appendChild(txt)

                    span = doc.createElement("span")
                    span.appendChild(doc.createTextNode("( "))
                    span.appendChild(elt)
                    span.appendChild(doc.createTextNode(" )"))
                    return span

                txt = doc.createTextNode("{0:,.2f}".format(value.value))
                elt.appendChild(txt)

                return elt

            # Sign and negativity of value is not the same.
            if value.value < 0:

                txt = doc.createTextNode("{0:,.2f}".format(-value.value))

                span = doc.createElement("span")
                span.appendChild(doc.createTextNode("( "))
                span.appendChild(txt)
                span.appendChild(doc.createTextNode(" )"))
                return span

            txt = doc.createTextNode("{0:,.2f}".format(value.value))
            return txt

        def add_nil_section(grid, section, periods):

            div = doc.createElement("div")
            div.setAttribute("class", "label header")
            div.appendChild(doc.createTextNode(section.header))
            grid.appendChild(div)

            for i in range(0, len(periods)):
                div = doc.createElement("div")
                div.setAttribute("class", "period total value nil")
                grid.appendChild(div)
                content = maybe_tag(0, section, i)
                div.appendChild(content)

        def add_total_section(grid, section, periods):

            div = doc.createElement("div")
            div.setAttribute("class", "label header total")
            div.appendChild(doc.createTextNode(section.header))
            grid.appendChild(div)

            for i in range(0, len(periods)):
                div = doc.createElement("div")
                grid.appendChild(div)
                value = section.total.values[i]
                if abs(value.value) < 0.001:
                    div.setAttribute("class", "period total value nil")
                elif value.value < 0:
                    div.setAttribute("class", "period total value negative")
                else:
                    div.setAttribute("class", "period total value")
                content = maybe_tag(value, section, i)
                div.appendChild(content)

        def add_breakdown_section(grid, section, periods):

            div = doc.createElement("div")
            div.setAttribute("class", "label breakdown header")
            div.appendChild(doc.createTextNode(section.header))
            grid.appendChild(div)

            for item in section.items:

                div = doc.createElement("div")
                div.setAttribute("class", "label breakdown item")
                div.appendChild(doc.createTextNode(item.description))
                grid.appendChild(div)

                for i in range(0, len(periods)):

                    value = item.values[i]

                    div = doc.createElement("div")
                    if abs(value.value) < 0.001:
                        div.setAttribute("class", "period value nil")
                    elif value.value < 0:
                        div.setAttribute("class", "period value negative")
                    else:
                        div.setAttribute("class", "period value")

                    content = maybe_tag(value, item, i)

                    div.appendChild(content)
                    grid.appendChild(div)

            div = doc.createElement("div")
            div.setAttribute("class", "label breakdown total")
            grid.appendChild(div)
            div.appendChild(doc.createTextNode("Total"))

            for i in range(0, len(periods)):

                div = doc.createElement("div")

                grid.appendChild(div)

                value = section.total.values[i]

                if abs(value.value) < 0.001:
                    div.setAttribute("class",
                                     "period value nil breakdown total")
                elif value.value < 0:
                    div.setAttribute("class",
                                     "period value negative breakdown total")
                else:
                    div.setAttribute("class", "period value breakdown total")

                content = maybe_tag(value, section, i)
                div.appendChild(content)

        def add_section(tbody, section, periods):

            if section.total == None and section.items == None:

                add_nil_section(tbody, section, periods)

            elif section.items == None:

                add_total_section(tbody, section, periods)

            else:

                add_breakdown_section(tbody, section, periods)

        def create_report(worksheet):

            ds = worksheet.get_dataset()
            periods = ds.periods
            sections = ds.sections

            grid = doc.createElement("div")
            grid.setAttribute("class", "sheet")

            add_header(grid, periods)

            for section in sections:

                add_section(grid, section, periods)

            return grid

        return create_report(worksheet)


