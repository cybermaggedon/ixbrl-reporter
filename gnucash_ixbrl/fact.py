
# iXBRL support for facts.  A Fact is a Datum mapped into the appropriate
# taxonomy.  So, context name will be a real iXBRL context.  Name will be the
# iXBRL tag name.

import json
import copy
from . period import Period
from . datum import *
from . context import Context
from lxml import objectify

class Fact:
    def use(self, fn):
        return fn(self)
    def append(self, maker, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        par.append(self.to_elt(maker, onlyifnamed))

class MoneyFact(Fact):
    def __init__(self, context, name, value, reverse=False, unit="GBP"):
        self.name = name
        self.value = value
        self.context = context
        self.unit = unit
        self.reverse = reverse
    def append(self, maker, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        value = self.value
        if self.reverse: value *= -1
        if self.name:
            elt = maker.nonFraction("{0:,.2f}".format(value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("unitRef", self.unit)
            elt.set("format", "ixt2:numdotdecimal")
            elt.set("decimals", "2")
            if value < 0:
                elt.set("sign", "-")
            par.append(elt)
        else:
            par.append(objectify.StringElement("{0:,.2f}".format(value)))
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
    def append(self, maker, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = maker.nonFraction(str(self.value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("unitRef", self.unit)
            elt.set("decimals", "0")
            par.append(elt)
        else:
            par.append(objectify.StringElement(self.value))

class NumberFact(Fact):
    def __init__(self, context, name, value, unit="pure"):
        self.context = context
        self.name = name
        self.value = value
        self.reverse = False
        self.unit = unit
    def append(self, maker, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = maker.nonFraction(str(self.value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("unitRef", self.unit)
            elt.set("decimals", "2")
            par.append(elt)
        else:
            par.append(objectify.StringElement(str(self.value)))

class StringFact(Fact):
    def __init__(self, context, name, value):
        self.value = value
        self.context = context
        self.name = name
    def to_elt(self, maker, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            # If value is list, assume it is list of elements
            if isinstance(self.value, list):
                elt = maker.nonNumeric()
                for v in self.value:
                    elt.append(v)
            else:
                elt = maker.nonNumeric(self.value)
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            return elt
        else:
            # If value is list, assume it is list of elements
            xhtml_ns = "http://www.w3.org/1999/xhtml"
            if isinstance(self.value, list):
                elt = maker.span(namespace=xhtml_ns)
                for v in self.value:
                    elt.append(v)
            else:
                elt = maker.span(self.value, namespace=xhtml_ns)
            return elt

class BoolFact(Fact):
    def __init__(self, context, name, value):
        self.value = bool(value)
        self.name = name
        self.context = context
    def append(self, maker, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = maker.nonNumeric(json.dumps(self.value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            par.append(elt)
        else:
            par.append(maker.StringElement(json.dumps(self.value)))

class DateFact(Fact):
    def __init__(self, context, name, value):
        self.context = context
        self.name = name
        self.value = value
    def append(self, maker, par, onlyifnamed=False):
        if onlyifnamed and not self.name: return
        if self.name:
            elt = maker.nonNumeric(self.value.strftime("%d\xa0%B\xa0%Y"))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("format", "ixt2:datedaymonthyearen")
            par.append(elt)
        else:
            par.append(objectify.StringElement(
                self.value.strftime("%d\xa0%B\xa0%Y")
            ))

class Dataset:
    pass

class Section:
    pass

class Series:
    def __init__(self, desc, values, rank=0):
        self.description = desc
        self.values = values
        self.rank = rank
