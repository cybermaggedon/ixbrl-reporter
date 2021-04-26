
# iXBRL support for facts.  A Fact is a Datum mapped into the appropriate
# taxonomy.  So, context name will be a real iXBRL context.  Name will be the
# iXBRL tag name.

import json
import copy
from . period import Period
from . datum import *
from . context import Context

class Fact:
    def use(self, fn):
        return fn(self)
    def append(self, doc, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        par.appendChild(self.to_elt(doc, onlyifnamed))

class MoneyFact(Fact):
    def __init__(self, context, name, value, reverse=False, unit="GBP"):
        self.name = name
        self.value = value
        self.context = context
        self.unit = unit
        self.reverse = reverse
    def append(self, doc, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        value = self.value
        if self.reverse: value *= -1
        if self.name:
            elt = doc.createElement("ix:nonFraction")
            elt.setAttribute("name", self.name)
            elt.setAttribute("contextRef", self.context)
            elt.setAttribute("unitRef", self.unit)
            elt.setAttribute("format", "ixt2:numdotdecimal")
            elt.setAttribute("decimals", "2")
            if value < 0:
                elt.setAttribute("sign", "-")
            elt.appendChild(doc.createTextNode("{0:,.2f}".format(value)))
            par.appendChild(elt)
        else:
            par.appendChild(doc.createTextNode("{0:,.2f}".format(value)))
    def copy(self):
        return copy.copy(self)
    def rename(self, id, context, tx):
        self.name = tx.get_tag_name(id)
        self.context = context
        self.reverse = tx.get_sign_reversed(id)

class CountFact(Fact):
    def __init__(self, context, name, value, unit="pure"):
        self.context = context
        self.name = name
        self.value = value
        self.reverse = False
        self.unit = unit
    def append(self, doc, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = doc.createElement("ix:nonFraction")
            elt.setAttribute("name", self.name)
            elt.setAttribute("contextRef", self.context)
            elt.setAttribute("unitRef", self.unit)
            elt.setAttribute("decimals", "0")
            elt.appendChild(doc.createTextNode(str(self.value)))
            par.appendChild(elt)
        else:
            par.appendChild(doc.createTextNode(str(self.value)))

class NumberFact(Fact):
    def __init__(self, context, name, value, unit="pure"):
        self.context = context
        self.name = name
        self.value = value
        self.reverse = False
        self.unit = unit
    def append(self, doc, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = doc.createElement("ix:nonFraction")
            elt.setAttribute("name", self.name)
            elt.setAttribute("contextRef", self.context)
            elt.setAttribute("unitRef", self.unit)
            elt.setAttribute("decimals", "2")
            elt.appendChild(doc.createTextNode(str(self.value)))
            par.appendChild(elt)
        else:
            par.appendChild(doc.createTextNode(str(self.value)))

class StringFact(Fact):
    def __init__(self, context, name, value):
        self.value = value
        self.context = context
        self.name = name
    def to_elt(self, doc, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = doc.createElement("ix:nonNumeric")
            elt.setAttribute("name", self.name)
            elt.setAttribute("contextRef", self.context)
            # If value is list, assume it is list of elements
            if isinstance(self.value, list):
                for e in self.value:
                    elt.appendChild(e)
            else:
                elt.appendChild(doc.createTextNode(self.value))
            return elt
        else:
            # If value is list, assume it is list of elements
            elt = doc.createElement("span")
            if isinstance(self.value, list):
                for e in self.value:
                    elt.appendChild(e)
            else:
                elt.appendChild(doc.createTextNode(self.value))
            return elt

class BoolFact(Fact):
    def __init__(self, context, name, value):
        self.value = bool(value)
        self.name = name
        self.context = context
    def append(self, doc, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = doc.createElement("ix:nonNumeric")
            elt.setAttribute("name", self.name)
            elt.setAttribute("contextRef", self.context)
            elt.appendChild(doc.createTextNode(json.dumps(self.value)))
            par.appendChild(elt)
        else:
            par.appendChild(doc.createTextNode(json.dumps(self.value)))

class DateFact(Fact):
    def __init__(self, context, name, value):
        self.context = context
        self.name = name
        self.value = value
    def append(self, doc, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = doc.createElement("ix:nonNumeric")
            elt.setAttribute("name", self.name)
            elt.setAttribute("contextRef", self.context)
            elt.setAttribute("format", "ixt2:datedaymonthyearen")
            elt.appendChild(doc.createTextNode(self.value.strftime("%d %B %Y")))
            par.appendChild(elt)
        else:
            par.appendChild(doc.createTextNode(self.value.strftime("%d %B %Y")))

class Dataset:
    pass

class Section:
    pass

class Series:
    def __init__(self, desc, values):
        self.description = desc
        self.values = values
