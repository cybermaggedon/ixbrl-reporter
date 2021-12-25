
# A Composite element is used to wrap several elements into a single document.

from . basic_element import BasicElement

class PageElement(BasicElement):
    def __init__(self, id, elts, data):
        super().__init__(id, data)
        self.elements = elts

    @staticmethod
    def load(elt_def, data):

        c = PageElement(
            elt_def.get("id", mandatory=False),
            [
                data.get_element(v)
                for v in elt_def.get("elements")
            ],
            data
        )
        return c

    def to_text(self, taxonomy, out):
        out.write("\n")
        for v in self.elements:
            v.to_text(taxonomy, out)
            out.write("\n")

    def to_debug(self, taxonomy, out):
        for v in self.elements:
            v.to_debug(taxonomy, out)
            out.write("\n")

    def to_ixbrl_elt(self, par, taxonomy):

        elt = par.xhtml_maker.div({
            "class": "page",
            "id": self.id + "-element"
        })

        for v in self.elements:

            sub = v.to_ixbrl_elt(par, taxonomy)
            for sub2 in sub:
                elt.append(sub2)
        
        return [elt]
