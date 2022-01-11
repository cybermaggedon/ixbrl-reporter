
# iXBRL support for facts.  A Fact is a Datum mapped into the appropriate
# taxonomy.  So, context name will be a real iXBRL context.  Name will be the
# iXBRL tag name.

import json
import copy
from . period import Period
from . datum import *
from . context import Context
from lxml import objectify

xhtml_ns = "http://www.w3.org/1999/xhtml"

class Fact:
    def use(self, fn):
        return fn(self)

class MoneyFact(Fact):
    def __init__(self, context, name, value, unit, scale, decimals,
                 reverse=False):
        self.name = name
        self.value = value
        self.context = context
        self.reverse = reverse
        self.unit = unit
        self.decimals = decimals
        self.scale = scale
    def to_elt(self, base):
        value = self.value
        if self.reverse: value *= -1
        if self.name:
            elt = base.ix_maker.nonFraction("{0:,.2f}".format(value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("unitRef", self.unit)
            elt.set("format", "ixt2:numdotdecimal")
            elt.set("decimals", str(self.decimals))
            elt.set("scale", str(self.scale))
            if value < 0:
                elt.set("sign", "-")
            return elt
        else:
            return base.xhtml_maker.span("{0:,.2f}".format(value))
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
    def to_elt(self, base):
        if self.name:
            elt = base.ix_maker.nonFraction(str(self.value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("unitRef", self.unit)
            elt.set("decimals", "0")
            return elt
        else:
            return base.xhtml_maker.span(self.value)

class NumberFact(Fact):
    def __init__(self, context, name, value, unit="pure"):
        self.context = context
        self.name = name
        self.value = value
        self.reverse = False
        self.unit = unit
    def to_elt(self, base):
        if self.name:
            elt = base.ix_maker.nonFraction(str(self.value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("unitRef", self.unit)
            elt.set("decimals", "2")
            return elt
        else:
            return base.xhtml_maker.span(str(self.value))

class StringFact(Fact):
    def __init__(self, context, name, value):
        self.value = value
        self.context = context
        self.name = name
    def to_elt(self, base):
        if self.name:
            # If value is list, assume it is list of elements
            if isinstance(self.value, list):
                elt = base.ix_maker.nonNumeric()
                for v in self.value:
                    elt.append(v)
            else:
                elt = base.ix_maker.nonNumeric(self.value)
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            return elt
        else:
            # If value is list, assume it is list of elements
            if isinstance(self.value, list):
                elt = base.xhtml_maker.span()
                for v in self.value:
                    elt.append(v)
            else:
                elt = base.xhtml_maker.span(self.value)
            return elt

class BoolFact(Fact):
    def __init__(self, context, name, value):
        self.value = bool(value)
        self.name = name
        self.context = context
    def to_elt(self, base):
        if self.name:
            elt = base.ix_maker.nonNumeric(json.dumps(self.value))
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            return elt
        else:
            return base.xhtml_maker.span(json.dumps(self.value))

class DateFact(Fact):
    def __init__(self, context, name, value):
        self.context = context
        self.name = name
        self.value = value
    def to_elt(self, base):
        if self.name:
            elt = base.ix_maker.nonNumeric(
                self.value.strftime("%d\xa0%B\xa0%Y")
            )
            elt.set("name", self.name)
            elt.set("contextRef", self.context)
            elt.set("format", "ixt2:datedaymonthyearen")
            return elt
        else:
            return base.xhtml_maker.span(
                self.value.strftime("%d\xa0%B\xa0%Y")
            )
