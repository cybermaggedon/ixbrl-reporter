
# Fact table is an Element which lists a set of facts.
from . period import Period
from . basicelement import BasicElement
from . fact import *
from . datum import *
from . worksheet import get_worksheet
import copy

from xml.dom.minidom import getDOMImplementation
from xml.dom import XHTML_NAMESPACE

from datetime import datetime, date
import json

class Box:
    def __init__(self, number, description, value, tag=None):
        self.number = number
        self.description = description
        self.value = value
        if tag == None:
            self.tag = {}
        else:
            self.tag = tag

business_type_name = {
    "company": "ct-comp:Company"
}

business_type = {
    "company": "Company"
}

class FactTable(BasicElement):

    def __init__(self, id, elts, title, data):
        super().__init__(id, data)
        self.elements = elts
        self.title = title

    @staticmethod
    def load(elt_def, data):

        c = FactTable(
            elt_def.get("id"),
            elt_def.get("facts"),
            elt_def.get("title", "Fact table"),
            data
        )
        return c

    def to_text(self, out):

        title = "*** {0} ***\n".format(self.title)
        out.write(title)
        
        for v in self.elements:
            datum = self.data.to_datum(v, None)
            out.write("{0}: {1}\n".format(datum.id, datum.value))

    def to_ixbrl_elt(self, par, taxonomy):

        div = par.doc.createElement("div")
        div.setAttribute("class", "facts page")
        div.setAttribute("id", self.id + "-element")

        title = par.doc.createElement("h2")
        title.appendChild(par.doc.createTextNode(self.title))
        div.appendChild(title)

        period = self.data.get_report_period()
        period_context = self.data.get_business_context().with_period(period)
        date_context = self.data.get_business_context().with_instant(
            self.data.get_report_date()
        )

        for v in self.elements:

            if v.get("context"):
                context = taxonomy.get_context(v.get("context"), self.data)
            else:
                context = period_context

            datum = self.data.to_datum(v, context)

            fact = taxonomy.create_fact(datum)
            elt = self.make_fact(par, v.get("field"),
                                 v.get("description"), fact)
            div.appendChild(elt)

        return div

    def make_fact(self, par, field, desc, fact):

        row = par.doc.createElement("div")
        row.setAttribute("class", "fact")

        num = par.doc.createElement("div")
        num.setAttribute("class", "ref")
        row.appendChild(num)
        num.appendChild(par.doc.createTextNode(field))

        descelt = par.doc.createElement("div")
        descelt.setAttribute("class", "description")
        row.appendChild(descelt)
        descelt.appendChild(par.doc.createTextNode(desc + ": "))

        valelt = par.doc.createElement("div")
        valelt.setAttribute("class", "value")
        row.appendChild(valelt)
        fact.append(par.doc, valelt)

        return row
