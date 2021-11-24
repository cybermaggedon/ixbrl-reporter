
# Notes element is a report element which displays notes.
from . basicelement import BasicElement
from . fact import *
from . note_parse import *
from lxml import objectify

from datetime import datetime

class NoteExpansion:

    def __init__(self, data):
        self.data = data

    def get_note_structure(self, n, taxonomy):

        return NoteParser.parse(n)

    def get_note(self, n, taxonomy):

        if n.startswith("note:"):
            return n[5:]

        note = taxonomy.get_note(n)
        if note:
            return note

        raise RuntimeError("Note '%s' not known." % n)

    def expand(self, input, par, taxonomy):
        
        period = self.data.get_report_period()
        rpc = self.data.business_context.with_period(period)

        elt = par.xhtml_maker.span()

        note = self.get_note(input, taxonomy)

        structure = self.get_note_structure(note, taxonomy)

        elements = [ elt ]

        for tk in structure:

            if isinstance(tk, TextToken):
                elements[-1].append(par.xhtml_maker.span(tk.text))

            elif isinstance(tk, MetadataToken):

                fact = taxonomy.get_metadata_by_id(self.data, tk.name)

                if fact:

                    if tk.prefix != "":
                        elements[-1].append(
                            par.xhtml_maker.span(tk.prefix)
                        )

                    elements[-1].append(fact.to_elt(par))

                    if tk.suffix != "":
                        elements[-1].append(
                            par.xhtml_maker.span(tk.suffix)
                        )

                else:

                    val = self.data.get_config(tk.name, mandatory=False)

                    # Metadata can be a config variable.
                    if val:
                        elements[-1].append(par.xhtml_maker.span(val))
                    else:
                        if tk.null != "":
                            elements[-1].append(par.xhtml_maker.span(tk.null))

            elif isinstance(tk, ComputationToken):

                if tk.period == "":
                    period = self.data.get_report_period()
                else:
                    period = Period.load(self.data.get_config(tk.period))

                res = self.data.perform_computations(period)

                datum = res.get(tk.name)

                fact = taxonomy.create_fact(datum)

                if fact:
                    elements[-1].append(fact.to_elt(par))

            elif isinstance(tk, TagOpen):

                if tk.kind != "string":
                    raise RuntimeError("Only string tags, currently")

                if tk.context == None:
                    ctxt = rpc
                else:
                    ctxt = taxonomy.get_context(tk.context, self.data)

                datum = StringDatum(tk.name, [], ctxt)
                fact = taxonomy.create_fact(datum)
                e = fact.to_elt(par)
                elements[-1].append(e)
                elements.append(e)

            elif isinstance(tk, TagClose):

                elements.pop()

        return [elt]


class NotesElement(BasicElement):
    def __init__(self, id, title, notes, numbered, data):
        super().__init__(id, data)
        self.title = title
        self.notes = notes
        self.numbered = numbered
        self.expander = NoteExpansion(data)

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

    def html_to_text(self, root, out):

        if root.tag == "{http://www.w3.org/1999/xhtml}span":
            if root.text: out.write(root.text)
        else:
            if root.text: out.write(root.text + "\n")

        for child in root.getchildren():
            self.html_to_text(child, out)

    def to_text(self, taxonomy, out):

        self.init_html(taxonomy)
        for note in self.notes:
            note = self.expand_text(note, self, taxonomy)

            if isinstance(note, str):
                out.write(note)
            else:
                for elt in note:
                    self.html_to_text(elt, out)
            out.write("\n")

    def expand_text(self, text, par, taxonomy):

        ne = NoteExpansion(self.data)
        return ne.expand(text, par, taxonomy)

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

            if self.numbered:

                li = par.xhtml_maker.li()
                contr.append(li)

                p = par.xhtml_maker.p()
                li.append(p)

            else:

                p = par.xhtml_maker.p()
                contr.append(p)

            elts = self.expander.expand(note, par, taxonomy)
            for elt in elts:
                p.append(elt)

        return [div]
