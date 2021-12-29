
# Entry point for Elements, Element.load calls out to appropriate code to
# construct elements.

from . worksheet_element import WorksheetElement
from . period import Period
from . composite import Composite
from . notes import NotesElement
from . note_heading import NoteHeading
from . html import HtmlElement
from . page import PageElement

class Element:

    @staticmethod
    def load(elt_def, data):

        kind = elt_def.get("kind")

        if kind == "composite":
            return Composite.load(elt_def, data)

        if kind == "worksheet":
            return WorksheetElement.load(elt_def, data)

        if kind == "notes":
            return NotesElement.load(elt_def, data)

        if kind == "noteheading":
            return NoteHeading.load(elt_def, data)

        if kind == "facttable":
            from . fact_table import FactTable
            return FactTable.load(elt_def, data)

        if kind == "page":
            return PageElement.load(elt_def, data)

        if kind == "html":
            return HtmlElement.load(elt_def, data)

        raise RuntimeError("Don't know element kind '%s'" % kind)

