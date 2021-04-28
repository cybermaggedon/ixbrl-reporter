
# A worksheet element is an element of a report which displays a worksheet.

from . basicelement import BasicElement
from . report import TextReporter
from . ixbrl import IxbrlReporter

class WorksheetElement(BasicElement):
    def __init__(self, id, title, worksheet, data):
        super().__init__(id, data)
        self.title = title
        self.worksheet = worksheet
        self.data = data

    @staticmethod
    def load(elt_def, data):

        e = WorksheetElement(
            elt_def.get("id"),
            elt_def.get("title"),
            data.get_worksheet(elt_def.get("worksheet")),
            data
        )

        return e

    def to_text(self, out):

        title = "*** {0} ***\n".format(self.title)
        out.write(title)
        
        rep = TextReporter()
        rep.output(self.worksheet, out)

        out.write("\n")

    def to_ixbrl_elt(self, par, taxonomy):

        rep = IxbrlReporter()
        elt = rep.get_elt(self.worksheet, par, taxonomy)

        div = par.doc.createElement("div")
        div.setAttribute("class", "worksheet page")
        elt.setAttribute("id", self.id + "-element")

        title = par.doc.createElement("h2")
        title.appendChild(par.doc.createTextNode(self.title))
        div.appendChild(title)

        div.appendChild(elt)
        
        return div
