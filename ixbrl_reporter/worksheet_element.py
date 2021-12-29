
# A worksheet element is an element of a report which displays a worksheet.

from . basic_element import BasicElement
from . text_reporter import TextReporter
from . debug_reporter import DebugReporter
from . ixbrl_reporter import IxbrlReporter
from lxml import objectify

class WorksheetElement(BasicElement):
    def __init__(self, id, title, worksheet, data, hide_notes=None):
        super().__init__(id, data)
        self.title = title
        self.worksheet = worksheet
        self.hide_notes = hide_notes
        self.data = data

    @staticmethod
    def load(elt_def, data):

        e = WorksheetElement(
            elt_def.get("id", mandatory=False),
            elt_def.get("title", mandatory=False),
            data.get_worksheet(elt_def.get("worksheet")),
            data,
            elt_def.get("hide-notes", False, mandatory=False)
        )

        return e

    def to_text(self, taxonomy, out):

        if self.title:
            title = "*** {0} ***\n".format(self.title)
            out.write(title)
        
        rep = TextReporter()
        rep.output(self.worksheet, out, taxonomy)
        out.write("\n")

    def to_debug(self, taxonomy, out):
        
        rep = DebugReporter()
        rep.output(self.worksheet, out, taxonomy)

    def to_ixbrl_elt(self, par, taxonomy):

        rep = IxbrlReporter(hide_notes = self.hide_notes)
        elt = rep.get_elt(self.worksheet, par, taxonomy, self.data)

        div = par.xhtml_maker.div()
        div.set("class", "worksheet")
        elt.set("id", self.id + "-element")

        if self.title:
            title = par.xhtml_maker.h2(self.title)
            div.append(title)

        div.append(elt)
        
        return [div]

