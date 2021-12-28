
# Fact table is an Element which lists a set of facts.
from . period import Period
from . basic_element import BasicElement
from . fact import *
from . datum import *
import copy

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

class FactTable(BasicElement):

    def __init__(self, id, elts, title, data):
        super().__init__(id, data)
        self.elements = elts
        self.title = title

    @staticmethod
    def load(elt_def, data):

        c = FactTable(
            elt_def.get("id", mandatory=False),
            elt_def.get("facts"),
            elt_def.get("title", "Fact table"),
            data
        )
        return c

    def to_text(self, taxonomy, out):

        title = "*** {0} ***\n".format(self.title)
        out.write(title)
        
        for v in self.elements:
            datum = self.data.to_datum(v, None)
            out.write("{0}: {1}\n".format(v.get("description"), datum.value))

    def to_ixbrl_elt(self, par, taxonomy):

        div = par.xhtml_maker.div()
        div.set("class", "facts")
        div.set("id", self.id + "-element")

        title = par.xhtml_maker.h2(self.title)
        div.append(title)

        period = self.data.get_report_period()
        period_context = self.data.get_business_context().with_period(period)
        date_context = self.data.get_business_context().with_instant(
            self.data.get_report_date()
        )

        for v in self.elements:

            if v.get("context"):
                context = taxonomy.get_context(v.get("context"))
            else:
                context = period_context

            datum = self.data.to_datum(v, context)

            if not datum:
                raise RuntimeError("Not valid: " + str(v))

            fact = taxonomy.create_fact(datum)

            elt = self.make_fact(par, v.get("field"),
                                 v.get("description"), fact)
            div.append(elt)

        return [div]

    def make_fact(self, par, field, desc, fact):

        row = par.xhtml_maker.div()
        row.set("class", "fact")

        num = par.xhtml_maker.div(field)
        num.set("class", "ref")
        row.append(num)

        descelt = par.xhtml_maker.div(desc + ":")
        descelt.set("class", "description")
        row.append(descelt)

        valelt = par.xhtml_maker.div()
        valelt.set("class", "factvalue")
        row.append(valelt)

        valelt.append(fact.to_elt(par))

        return row
