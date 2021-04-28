
# Notes element is a report element which displays notes.
from . basicelement import BasicElement
from . fact import *
from . note_parse import *

from datetime import datetime

class NotesElement(BasicElement):
    def __init__(self, id, title, notes, data):
        super().__init__(id, data)
        self.title = title
        self.notes = notes

    @staticmethod
    def load(elt_def, data):

        e = NotesElement(
            elt_def.get("id"),
            elt_def.get("title", "Notes"),
            elt_def.get("notes"),
            data
        )

        return e

    def to_text(self, out):

        # FIXME: Put notes out as text.
        pass

    def get_note_elts(self, n, par, taxonomy):
        
        period = self.data.get_report_period()
        rpc = self.data.business_context.with_period(period)

        elt = par.doc.createElement("span")

        note = self.get_note(n, taxonomy)

        structure = self.get_note_structure(note, taxonomy)

        elements = [ elt ]

        for tk in structure:

            if isinstance(tk, TextToken):
                elements[-1].appendChild(par.doc.createTextNode(tk.text))

            elif isinstance(tk, MetadataToken):

                fact = taxonomy.get_metadata_by_id(self.data, tk.name)

                if fact:

                    if tk.prefix != "":
                        elements[-1].appendChild(
                            par.doc.createTextNode(tk.prefix)
                        )

                    fact.append(par.doc, elements[-1])

                    if tk.suffix != "":
                        elements[-1].appendChild(
                            par.doc.createTextNode(tk.suffix)
                        )

                else:

                    if tk.null != "":
                        elements[-1].appendChild(par.doc.createTextNode(tk.null))
            elif isinstance(tk, ComputationToken):

                if tk.period == "":
                    period = self.data.get_report_period()
                else:
                    period = Period.load(self.data.get_config(tk.period))

                res = self.data.perform_computations(period)

                datum = res.get(tk.name)

                fact = taxonomy.create_fact(datum)

                if fact:
                    fact.append(par.doc, elements[-1])

            elif isinstance(tk, TagOpen):

                if tk.kind != "string":
                    raise RuntimeError("Only string tags, currently")

                if tk.context == None:
                    ctxt = rpc
                else:
                    ctxt = taxonomy.get_context(tk.context, self.data)

                datum = StringDatum(tk.name, [], ctxt)
                fact = taxonomy.create_fact(datum)
                e = fact.to_elt(par.doc)
                elements[-1].appendChild(e)
                elements.append(e)

            elif isinstance(tk, TagClose):

                elements.pop()

        return elt

    def get_note_structure(self, n, taxonomy):

        return NoteParser.parse(n)

    def get_note(self, n, taxonomy):

        if n.startswith("note:"):
            return n[5:]

        note = taxonomy.get_note(n)
        if note:
            return note

        raise RuntimeError("Note '%s' not known." % n)

    def to_ixbrl_elt(self, par, taxonomy):

        div = par.doc.createElement("div")
        div.setAttribute("class", "notes page")
        div.setAttribute("id", self.id + "-element")

        title = par.doc.createElement("h2")
        if self.title:
            title.appendChild(par.doc.createTextNode(self.title))
        else:
            title.appendChild(par.doc.createTextNode("Notes"))
        div.appendChild(title)

        ol = par.doc.createElement("ol")
        div.appendChild(ol)

        for note in self.notes:

            li = par.doc.createElement("li")
            ol.appendChild(li)

            p = par.doc.createElement("p")
            li.appendChild(p)

            p.appendChild(self.get_note_elts(note, par, taxonomy))

        return div
