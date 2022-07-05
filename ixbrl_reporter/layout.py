
from . datum import StringDatum
from . worksheet_element import WorksheetElement

class Elt:

    @staticmethod
    def load(root, data):

        if isinstance(root, str):
            return data.expand_string(root)

        if "tag" in root:
            return TagElt.load(root, data)

        if "fact" in root:
            return FactElt.load(root, data)

        if "element" in root:
            return ElementElt.load(root, data)

        if "worksheet" in root:
            return WorksheetElt.load(root, data)

        if "ifdef" in root:
            return IfdefElt.load(root, data)

        raise RuntimeError("Can't handle ", root)


class TagElt(Elt):
    def __init__(self, tag, attrs, content, data):
        self.tag = tag
        self.attrs = attrs
        self.content = content
        self.data = data

    @staticmethod
    def load(root, data):
        tag = root.get("tag")
        attrs = root.get("attributes", {}, mandatory=False)
        content = root.get("content", [], mandatory=False)

        if isinstance(content, str):
            content = [Elt.load(content, data)]
        elif isinstance(content, list):
            content = [Elt.load(v, data) for v in content]
        elif isinstance(content, dict):
            content = [Elt.load(content, data)]
        else:
            raise RuntimeError(
                "Can't handle content being type %s" % str(type(content))
            )

        return TagElt(tag, attrs, content, data)

    def to_html(self, par, taxonomy):

        elt = par.xhtml_maker(self.tag, self.attrs)

        for c in self.content:
            elt2 = c.to_html(par, taxonomy)
            if elt2 is not None: elt.append(elt2)

        return elt

    def to_text(self, taxonomy, out):

        for c in self.content:
            c.to_text(taxonomy, out)

        if self.tag.lower() in {
                "div", "p", "td", "br", "tr", "h1", "h2", "h3"
        }:
            out.write("\n")
         
        if self.tag.lower() in {
                "hr"
        }:
            out.write("--------\n")

    def to_debug(self, taxonomy, out):

        for c in self.content:
            c.to_debug(taxonomy, out)

        print("tag:", self.tag.lower())

class IfdefElt(Elt):
    def __init__(self, key, content, data):
        self.key = key
        self.content = content
        self.data = data

    @staticmethod
    def load(root, data):
        key = root.get("ifdef")
        content = root.get("content")
        content = Elt.load(content, data)
        return IfdefElt(key, content, data)

    def to_html(self, par, taxonomy):

        try:
            self.data.get_config(self.key)
        except:
            return None

        return self.content.to_html(par, taxonomy)

    def to_text(self, taxonomy, out):
        try:
            self.data.get_config(self.key)
        except:
            return

        self.content.to_text(taxonomy, out)

    def to_debug(self, taxonomy, out):
        try:
            self.data.get_config(self.key)
        except:
            return

        self.content.to_debug(taxonomy, out)

class MetadataElt(Elt):
    def __init__(self, name, prefix, suffix, null, data):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.null = null
        self.data = data

    def to_html(self, par, taxonomy):

        elt = par.xhtml_maker.span()

        fact = taxonomy.get_metadata_by_id(self.name)
        if fact:
            if self.prefix != "":
                elt.append(par.xhtml_maker.span(self.prefix))
            elt.append(fact.to_elt(par))
            if self.suffix != "":
                elt.append(par.xhtml_maker.span(self.suffix))
            return elt

        val = self.data.get_config(self.name, mandatory=False)
        if val:
            if self.prefix != "":
                elt.append(par.xhtml_maker.span(self.prefix))
            elt.append(par.xhtml_maker.span(str(val)))
            if self.suffix != "":
                elt.append(par.xhtml_maker.span(self.suffix))
            return elt

        return par.xhtml_maker.span(self.null)

    def to_text(self, taxonomy, out):

        fact = taxonomy.get_metadata_by_id(self.name)
        if fact:
            if self.prefix != "": out.write(self.prefix)
            out.write(str(fact.value))
            if self.suffix != "": out.write(self.suffix)
            return

        val = self.data.get_config(self.name, mandatory=False)
        if val:
            if self.prefix != "": out.write(self.prefix)
            out.write(val)
            if self.suffix != "": out.write(self.suffix)
            return

    def to_debug(self, taxonomy, out):

        fact = taxonomy.get_metadata_by_id(self.data, self.name)
        if fact:
            if self.prefix != "": out.write(self.prefix)
            out.write(str(fact.value))
            if self.suffix != "": out.write(self.suffix)
            return

        val = self.data.get_config(self.name, mandatory=False)
        if val:
            if self.prefix != "": out.write(self.prefix)
            out.write(val)
            if self.suffix != "": out.write(self.suffix)
            return

class StringElt(Elt):
    def __init__(self, value, data):
        self.value = value
        self.data = data

    @staticmethod
    def load(value, data):
        return StringElt(value, data)

    def to_html(self, par, taxonomy):
        return par.xhtml_maker.span(self.value)

    def to_text(self, taxonomy, out):
        out.write(self.value)
        return

    def to_debug(self, taxonomy, out):
        out.write(self.value)
        return

class FactElt(Elt):
    def __init__(self, fact, ctxt, attrs, content, data):
        self.fact = fact
        self.ctxt = ctxt
        self.attrs = attrs
        self.content = content
        self.data = data
    @staticmethod
    def load(root, data):
        fact = root.get("fact")
        attrs = root.get("attributes", {}, mandatory=False)
        content = root.get("content", [], mandatory=False)

        if isinstance(content, str):
            content = [Elt.load(content, data)]
        elif isinstance(content, list):
            content = [Elt.load(v, data) for v in content]
        elif isinstance(content, dict):
            content = [Elt.load(content, data)]
        else:
            raise RuntimeError(
                "Can't handle content being type %s" % str(type(content))
            )

        ctxt = root.get("context")
        return FactElt(fact, ctxt, attrs, content, data)

    def to_html(self, par, taxonomy):

        if self.ctxt == None:
            period = self.data.get_report_period()
            ctxt = self.data.business_context.with_period(period)
        else:
            ctxt = taxonomy.get_context(self.ctxt)
        datum = StringDatum(self.fact, [], ctxt)
        fact = taxonomy.create_fact(datum)
        elt = fact.to_elt(par)

        for child in self.content:
            elt2 = child.to_html(par, taxonomy)
            if elt2 is not None: elt.append(elt2)

        return elt

    def to_text(self, taxonomy, out):

        for child in self.content:
            child.to_text(taxonomy, out)

        return

    def to_debug(self, taxonomy, out):

        for child in self.content:
            child.to_debug(taxonomy, out)

        return

class ElementElt(Elt):
    def __init__(self, elt, data):
        self.elt = elt
        self.data = data
    @staticmethod
    def load(root, data):
        element = root.get("element")

        if isinstance(element, str):
            return ElementElt(data.get_element(element), data)
        elif isinstance(element, dict):
            return ElementElt(data.get_element(element), data)
        else:        
            raise RuntimeError(
                "Can't handle element being type %s" % str(type(content))
            )

    def to_html(self, par, taxonomy):

        content = self.elt.to_ixbrl_elt(par, taxonomy)
        
        cntr = par.xhtml_maker.div()
        for c in content:
            if c is not None:
                cntr.append(c)

        return cntr

    def to_text(self, taxonomy, out):
        self.elt.to_text(taxonomy, out)

    def to_debug(self, taxonomy, out):
        self.elt.to_debug(taxonomy, out)

class WorksheetElt(Elt):

    def __init__(self, ws, data):
        self.wse = ws
        self.data = data

    @staticmethod
    def load(root, data):
        wse = WorksheetElement.load(root, data)
        return WorksheetElt(wse, data)

    def to_html(self, par, taxonomy):

        # Assumption about WorksheetElement: Returns single element in list
        return self.wse.to_ixbrl_elt(par, taxonomy)[0]

    def to_text(self, taxonomy, out):
        self.wse.to_text(taxonomy, out)

    def to_debug(self, taxonomy, out):
        self.wse.to_debug(taxonomy, out)

class ComputationElt(Elt):
    def __init__(self, name, period, data):
        self.ctxt = None
        self.name = name
        self.period = period
        self.data = data

    def to_html(self, par, taxonomy):

        elt = par.xhtml_maker.span()

        if self.period == "":
            period = self.data.get_report_period(0)
        else:
            period = self.data.get_period(self.period)

        res = self.data.get_result(self.name, period)

        if self.ctxt == None:
            ctxt = self.data.business_context.with_period(period)
        else:
            ctxt = taxonomy.get_context(self.ctxt)

        fact = taxonomy.create_fact(res)

        elt = fact.to_elt(par)

        return elt

    def to_text(self, taxonomy, out):

        elt = par.xhtml_maker.span()

        if self.period == "":
            period = self.data.get_report_period(0)
        else:
            period = self.data.get_period(self.period)

        res = self.data.get_result(self.name, period)

        if self.ctxt == None:
            ctxt = self.data.business_context.with_period(period)
        else:
            ctxt = taxonomy.get_context(self.ctxt)

        fact = taxonomy.create_fact(res)

        out.write(fact.to_text())

    def to_debug(self, taxonomy, out):

        self.to_text(taxonomy, out)

