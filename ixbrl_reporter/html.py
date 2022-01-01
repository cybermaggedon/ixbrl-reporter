
from . basic_element import BasicElement
from . layout import *

from lxml import objectify, etree

class HtmlElement(BasicElement):
    def __init__(self, id, root, data):
        super().__init__(id, data)
        self.root = root

    @staticmethod
    def load(elt_def, data):

        id = elt_def.get("id", mandatory=False)
        root = elt_def.get("root")
        root = Elt.load(root, data)

        c = HtmlElement(id, root, data)

        return c

    def to_text(self, taxonomy, out):

        self.root.to_text(taxonomy, out)

    def to_html_elt(self, root, taxonomy, out):
        return root.to_html(taxonomy, out)

    def to_debug(self, taxonomy, out):
        self.root.to_debug(taxonomy, out)

    def to_ixbrl_elt(self, par, taxonomy):

        root = self.root

        return [self.to_html_elt(root, par, taxonomy)]

