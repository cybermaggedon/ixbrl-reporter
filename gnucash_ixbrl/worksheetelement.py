
# A worksheet element is an element of a report which displays a worksheet.

from . basicelement import BasicElement
from . report import TextReporter
from . worksheet_ixbrl import IxbrlReporter
from lxml import objectify

class WorksheetElement(BasicElement):
    def __init__(self, id, title, worksheet, data):
        super().__init__(id, data)
        self.title = title
        self.worksheet = worksheet
        self.data = data

    @staticmethod
    def load(elt_def, data):

        e = WorksheetElement(
            elt_def.get("id", mandatory=False),
            elt_def.get("title", mandatory=False),
            data.get_worksheet(elt_def.get("worksheet")),
            data
        )

        return e

    def to_text(self, taxonomy, out):

        if self.title:
            title = "*** {0} ***\n".format(self.title)
            out.write(title)
        
        rep = TextReporter()
        rep.output(self.worksheet, out)

        out.write("\n")

    def to_ixbrl_elt(self, par, taxonomy):

        rep = IxbrlReporter()
        elt = rep.get_elt(self.worksheet, par, taxonomy)

        div = par.xhtml_maker.div()
        div.set("class", "worksheet")
        elt.set("id", self.id + "-element")

        if self.title:
            title = par.xhtml_maker.h2(self.title)
            div.append(title)

        div.append(elt)
        
        return [div]
