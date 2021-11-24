
# A Composite element is used to wrap several elements into a single document.

from . basicelement import BasicElement
from . notes import NoteExpansion
from . datum import StringDatum
from . worksheetelement import WorksheetElement
from lxml import objectify, etree

class HtmlElement(BasicElement):
    def __init__(self, id, root, data):
        super().__init__(id, data)
        self.root = root

    @staticmethod
    def load(elt_def, data):

        c = HtmlElement(
            elt_def.get("id", mandatory=False),
            elt_def.get("root"),
            data
        )
        return c

    def html_to_text(self, root, out):

        if root.tag == "{http://www.w3.org/1999/xhtml}span":
            if root.text: out.write(root.text)
        else:
            if root.text: out.write(root.text + "\n")

        for child in root.getchildren():
            self.html_to_text(child, out)

    def write_text(self, root, out, taxonomy):

        content = root.get("content", mandatory=False)

        if not content:
            content = []
            
        if isinstance(content, str):

            content = self.expand_text(content, self, taxonomy)

            if isinstance(content, str):
                out.write(content + "\n")
            else:
                for elt in content:
                    self.html_to_text(elt, out)

            return

        for child in content:

            if isinstance(child, str):
                child = self.expand_text(child, self, taxonomy)

                if isinstance(child, str):
                    out.write(child + "\n")
                else:
                    for child2 in child:
                        self.html_to_text(child2, out)

            elif isinstance(child, dict):
                self.write_text(child, out, taxonomy)
            else:
                raise RuntimeError(
                    "HTMLElement can't work with content of type %s" %
                    str(type(child))
                )

    def to_text(self, taxonomy, out):

        self.init_html(taxonomy)
        self.write_text(self.root, out, taxonomy)

    def expand_text(self, text, par, taxonomy):

        if not text.startswith("expand:"): return text

        ne = NoteExpansion(self.data)
        return ne.expand(text[7:], par, taxonomy)

    def to_html(self, root, par, taxonomy):

        tag = root.get("tag", mandatory=False)
        fact = root.get("fact", mandatory=False)
        worksheet = root.get("worksheet", mandatory=False)

        if worksheet:
            ws = self.data.get_worksheet(worksheet)
            wse = WorksheetElement(None, None, ws, self.data)

            # Assumption about WorksheetElement: Returns single element in list
            return wse.to_ixbrl_elt(par, taxonomy)[0]

        if tag == None and fact == None:
            raise RuntimeError("HTML elements must have a tag or fact property")

        attrs = root.get("attributes", mandatory=False)
        content = root.get("content", mandatory=False)

        if not attrs:
            attrs = {}

        if not content:
            content = []

        if fact:
            context_id = root.get("context")
            ctxt = taxonomy.get_context(context_id, self.data)

        if isinstance(content, int):
            content = str(content)
        if isinstance(content, float):
            content = str(content)

        # The content element is a string
        if isinstance(content, str):

            content = self.expand_text(content, par, taxonomy)

            if isinstance(content, str):

                # Expands to a string
                if fact:
                    datum = StringDatum(fact, content, ctxt)
                    fact = taxonomy.create_fact(datum)
                    return fact.to_elt(par)
                else:
                    return par.xhtml_maker(tag, attrs, content)

            else:

                # Expands to a list of elements
                elt = par.xhtml_maker(tag, attrs)
                for child in content:
                    elt.append(child)
                return elt

        # The content element is an array of elts.

        # If fact, parent elt is a fact tag
        if fact:
            datum = StringDatum(fact, [], ctxt)
            fact = taxonomy.create_fact(datum)
            elt = fact.to_elt(par)
        else:
            elt = par.xhtml_maker(tag, attrs)

        for child in content:
            if isinstance(child, str):
                child = self.expand_text(child, par, taxonomy)
                if isinstance(child, str):
                    elt.append(par.xhtml_maker.span(child))
                else:
                    for child2 in child:
                        if isinstance(child2, str):
                            elt.append(par.xhtml_maker.span(child2))
                        else:
                            elt.append(child2)
            elif isinstance(child, dict):
                elt.append(self.to_html(child, par, taxonomy))
            else:
                raise RuntimeError(
                    "HTMLElement can't work with content of type %s" %
                    str(type(child))
                )

        return elt

    def to_ixbrl_elt(self, par, taxonomy):

        root = self.root

        return [self.to_html(root, par, taxonomy)]

