
# A Composite element is used to wrap several elements into a single document.

from . basicelement import BasicElement

class Composite(BasicElement):
    def __init__(self, id, elts, data):
        super().__init__(id, data)
        self.elements = elts

    @staticmethod
    def load(elt_def, data):

        c = Composite(
            elt_def.get("id"),
            [
                data.get_element(v)
                for v in elt_def.get("elements")
            ],
            data
        )
        return c

    def to_text(self, out):
        out.write("\n")
        for v in self.elements:
            v.to_text(out)
            out.write("\n")

    def to_ixbrl_elt(self, par, taxonomy):

        elt = par.doc.createElement("div")
        elt.setAttribute("class", "composite")
        elt.setAttribute("id", self.id + "-element")

        for v in self.elements:

            sub = v.to_ixbrl_elt(par, taxonomy)
            elt.appendChild(sub)
        
        return elt
