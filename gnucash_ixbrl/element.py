
# Entry point for Elements, Element.load calls out to appropriate code to
# construct elements.

from . worksheet import get_worksheet
from . worksheetelement import WorksheetElement
from . period import Period
from . composite import Composite
from . title import Title
from . notes import NotesElement

class Element:

    @staticmethod
    def load(elt_def, data):

        kind = elt_def.get("kind")

        if kind == "composite":
            return Composite.load(elt_def, data)

        if kind == "title":
            return Title.load(elt_def, data)

        if kind == "worksheet":
            return WorksheetElement.load(elt_def, data)

        if kind == "notes":
            return NotesElement.load(elt_def, data)

        if kind == "facttable":
            from . facttable import FactTable
            return FactTable.load(elt_def, data)

        raise RuntimeError("Don't know element kind '%s'" % kind)

