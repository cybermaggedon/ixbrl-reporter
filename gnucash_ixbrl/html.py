
# A Composite element is used to wrap several elements into a single document.

from . basicelement import BasicElement
from . notes import NoteExpansion

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

    def write_text(self, root, out):

        content = root.get("content", mandatory=False)

        if not content:
            content = []
            
        if isinstance(content, str):
            out.write(content + "\n")
            return

        for child in content:
            if isinstance(child, str):
                out.write(child + "\n")

            elif isinstance(child, dict):
                self.write_text(child, out)
            else:
                raise RuntimeError(
                    "HTMLElement can't work with content of type %s" %
                    str(type(child))
                )

    def to_text(self, out):

        self.write_text(self.root, out)

    def expand_text(self, text, par, taxonomy):

        if not text.startswith("expand:"): return text

        ne = NoteExpansion(self.data)
        return ne.expand(text[7:], par, taxonomy)

    def to_html(self, root, par, taxonomy):

        tag = root.get("tag")
        attrs = root.get("attributes", mandatory=False)
        content = root.get("content", mandatory=False)

        if not attrs:
            attrs = {}

        if not content:
            content = []
            
        if isinstance(content, str):
            content = self.expand_text(content, par, taxonomy)
            return par.xhtml_maker(tag, attrs, content)

        elt = par.xhtml_maker(tag, attrs)

        for child in content:
            if isinstance(child, str):
                content = self.expand_text(child, par, taxonomy)
                elt.append(par.xhtml_maker.span(content))
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

