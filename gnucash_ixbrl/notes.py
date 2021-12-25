
# Notes element is a report element which displays notes.
from . basic_element import BasicElement
from . fact import *

class NotesElement(BasicElement):
    def __init__(self, id, title, notes, numbered, data):
        super().__init__(id, data)
        self.title = title
        self.notes = notes
        self.numbered = numbered

    @staticmethod
    def load(elt_def, data):

        e = NotesElement(
            elt_def.get("id", mandatory=False),
            elt_def.get("title", mandatory=False),
            elt_def.get("notes"),
            elt_def.get("numbered", True, mandatory=False),
            data
        )

        return e

    def to_text(self, taxonomy, out):

        for note in self.notes:

            elt = self.data.expand_string(note)
            elt.to_text(taxonomy, out)
            out.write("\n")

    def to_debug(self, taxonomy, out):

        for note in self.notes:

            elt = self.data.expand_string(note)
            elt.to_debug(taxonomy, out)
            out.write("\n")

    def to_ixbrl_elt(self, par, taxonomy):

        div = par.xhtml_maker.div()
        div.set("class", "notes")
        div.set("id", self.id + "-element")

        if self.title:
            title = par.xhtml_maker.h2(self.title)
            div.append(title)

        if self.numbered:
            contr = par.xhtml_maker.ol()
        else:
            contr = par.xhtml_maker.div()

        div.append(contr)

        for note in self.notes:

            nelt = self.data.expand_string(note)

            if self.numbered:

                li = par.xhtml_maker.li()
                contr.append(li)

                p = par.xhtml_maker.p()
                li.append(p)

            else:

                p = par.xhtml_maker.p()
                contr.append(p)

            p.append(nelt.to_html(par, taxonomy))

        return [div]
