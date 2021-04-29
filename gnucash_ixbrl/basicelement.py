
# Base class for elements.  Any element can be output as an iXBRL document.
# There is code here which handles the standard 'outer' iXBRL document
# and global context management.
from . period import Period
from . fact import *

from xml.dom.minidom import getDOMImplementation
from xml.dom import XHTML_NAMESPACE
import json
from datetime import datetime

class BasicElement:

    def __init__(self, id, data):
        self.id = id
        self.data = data

    @staticmethod
    def load(elt_def, data):

        kind = elt_def.get("kind")

        if kind == "composite":
            from . composite import Composite
            return Composite.load(elt_def, data)

        if kind == "title":
            from . title import Title
            return Title.load(elt_def, data)

        if kind == "worksheet":
            from . worksheetelement import WorksheetElement
            return WorksheetElement.load(elt_def, data)

        if kind == "notes":
            from . notes import NotesElement
            return NotesElement.load(elt_def, data)

        if kind == "facttable":
            from . facttable import FactTable
            return FactTable.load(elt_def, data)

        raise RuntimeError("Don't know element kind '%s'" % kind)

    def add_style(self, elt):

        doc = self.doc
        
        style = doc.createElement("style")
        style.setAttribute("type", "text/css")
        elt.appendChild(style)
            
        style_text = """

h2 {
  page-break-before: always;
}

@media screen, projection, tv {

  body {
    margin: 2% 4% 2% 4%;
    background-color: gray;
  }

  DIV.page {

    background-color: white;
    padding: 2em;

    /* CSS hack for cross browser minimum height */
    min-height: 29.7cm;

    height: 29.7cm;
    width: 21cm;

    margin: 2em 0;

  }

  DIV.title.page h1 {
    margin: 4rem 4rem 0.5rem 4rem;
    padding: 0;
  }

  DIV.title.page DIV.subheading {
    font-weight: bold;
    margin: 0.5rem 4em 2rem 4em;
    padding: 0;
  }

  DIV.title.page DIV.information {
    margin: 0.2em 4em 0.2em 4em;
    padding: 0;
  }

  DIV.title.page DIV.signature {
    padding: 4rem;
  }

}

.sheet {
  display: grid;
  grid-template-columns: 20rem repeat(10, 10rem);
  grid-template-rows: auto;
  column-gap: 1rem;
  row-gap: 0.2rem;
  padding: 1rem;
}

.header {
  font-weight: bold;
  margin-top: 1em;
}

.label {
  grid-column: 1;
}

.label.breakdown.header {
  grid-column: 1 / span 10;
}

.label.item {
  padding-left: 2em;
}

.value {
  font-family: Source Code Pro, monospace;
  font-size: 10pt;
}

@media print {
  .value {
    font-family: Source Code Pro, monospace;
    font-size: 1rem;
  }
  * {
    font-size: 1rem;
  }
  .sheet {
    grid-template-columns: 40% repeat(10, 20%);
  }
}

.total.value {
  margin-top: 1em;
}

.breakdown.total {
  margin-top: 0.2em;
  padding-top: 4px;
  border-top: 1px solid white;
}

.breakdown.total.value {
  border-top: 1px solid #808080;
}

.periodname {
  padding: 0.5em 1em 0.5em 1em;
  border-bottom: 0.2em solid black;
  font-weight: bold;
  justify-self: stretch;
  align-self: stretch;
  text-align: center;
}

.currency {
  justify-self: end;
  padding-right: 1em;
}

.period.value {
  text-align: right;
  padding-right: 2.2em;
}

.period.value.negative {
  color: #400000;
  padding-right: 1em;
}

.period.value.nil {
  color: #a0a0a0;
}

.hidden {
  display: none;
}



.fact {
  display: flex;
  flex-direction: row;
  margin: 2px;
}

.fact DIV {
  margin: 0rem 1rem 0rem 1rem;
  padding: 4px;
}

.fact .ref {
  width: 5rem;
  text-align: center;
  color: white;
  background-color: #2ca469;
  border: 2px solid #104020;
  font-weight: bold;
  padding-left: 0.2rem;
  padding-right: 0.2rem;
}

.fact .description {
  width: 25em;
}

.fact .value {
  border: 2px solid black;
  background-color: white;
}

.fact .value.false {
  color: #a0a0a0;
}
        """

        style.appendChild(doc.createTextNode(style_text))

    def to_html(self, out):

        impl = getDOMImplementation()

        self.periods = [
            Period.load(v)
            for v in self.cfg.get("metadata.report.periods")
        ]
        
        doc = impl.createDocument(None, "html", None)
        self.doc = doc

        html = self.doc.documentElement

        html.setAttribute("xmlns", XHTML_NAMESPACE)

        self.html = html

        head = doc.createElement("head")
        html.appendChild(head)

        self.add_style(head)

        body = doc.createElement("body")
        html.appendChild(body)

        elt = self.to_ixbrl_elt(self)

        def walk(elt):
            if elt.nodeType == elt.ELEMENT_NODE:

                # Remove ixbrl stuff, just turn tags into span tags.
                if elt.tagName[:3] == "ix:":
                    try:
                        elt.removeAttribute("contextRef")
                    except: pass
                    try:
                        elt.removeAttribute("name")
                    except: pass
                    try:
                        elt.removeAttribute("format")
                    except: pass
                    try:
                        elt.removeAttribute("unitRef")
                    except: pass
                    try:
                        elt.removeAttribute("decimals")
                    except: pass
                    elt.tagName = "span"
                if elt.childNodes:
                    for e in elt.childNodes:
                        walk(e)

        walk(elt)

        body.appendChild(elt)

        if self.cfg.get_bool("metadata.report.pretty-print"):
            out.write(doc.toprettyxml())
        else:
            out.write(doc.toxml())

    def to_ixbrl(self, taxonomy, out):

        impl = getDOMImplementation()
        
        doc = impl.createDocument(None, "html", None)

        self.doc = doc

        html = self.doc.documentElement

        html.setAttribute("xmlns", XHTML_NAMESPACE)

        html.setAttribute("xmlns:ix", "http://www.xbrl.org/2013/inlineXBRL")
        html.setAttribute("xmlns:link", "http://www.xbrl.org/2003/linkbase")
        html.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink")
        html.setAttribute("xmlns:xbrli", "http://www.xbrl.org/2003/instance")
        html.setAttribute("xmlns:xbrldi", "http://xbrl.org/2006/xbrldi")
        html.setAttribute("xmlns:ixt2",
                          "http://www.xbrl.org/inlineXBRL/transformation/2011-07-31")
        html.setAttribute("xmlns:iso4217", "http://www.xbrl.org/2003/iso4217")

        ns = taxonomy.get_namespaces()
        for k in ns:
            html.setAttribute("xmlns:" + k, ns[k])

        self.html = html

        head = doc.createElement("head")
        html.appendChild(head)

        def add_title(val):
            t = doc.createElement("title");
            t.appendChild(doc.createTextNode(val));
            head.appendChild(t)

        self.data.get_config("metadata.report.title").use(add_title)

        self.add_style(head)

        body = doc.createElement("body")
        html.appendChild(body)

        hiddev = doc.createElement("div")
        hiddev.setAttribute("class", "hidden")
        body.appendChild(hiddev)

        hdr = doc.createElement("ix:header")
        hiddev.appendChild(hdr)

        hidden = doc.createElement("ix:hidden")
        hdr.appendChild(hidden)
        self.hidden = hidden

        refs = doc.createElement("ix:references")
        hdr.appendChild(refs)
       
        resources = doc.createElement("ix:resources")
        hdr.appendChild(resources)
        self.resources = resources

        # This creates some contexts, hence do this first.
        self.create_metadata(taxonomy)

        schemas = taxonomy.get_schemas()
        for url in schemas:
            schema = doc.createElement("link:schemaRef")
            schema.setAttribute("xlink:type", "simple")
            schema.setAttribute("xlink:href", url)
            schema.appendChild(doc.createTextNode(""))
            refs.appendChild(schema)

        elt = self.to_ixbrl_elt(self, taxonomy)
        body.appendChild(elt)

        # Contexts get created above, hence do this last.
        self.create_contexts(taxonomy)

        currency = self.data.get_config("metadata.report.currency")

        unit = doc.createElement("xbrli:unit")
        unit.setAttribute("id", currency)
        measure = doc.createElement("xbrli:measure")
        measure.appendChild(doc.createTextNode("iso4217:" + currency))
        unit.appendChild(measure)
        resources.appendChild(unit)

        unit = doc.createElement("xbrli:unit")
        unit.setAttribute("id", "pure")
        measure = doc.createElement("xbrli:measure")
        measure.appendChild(doc.createTextNode("xbrli:pure"))
        unit.appendChild(measure)
        resources.appendChild(unit)
       
        if self.data.get_config_bool("metadata.report.pretty-print",
                                     mandatory=False):
            out.write(doc.toprettyxml())
        else:
            out.write(doc.toxml())

    def create_contexts(self, taxonomy):

        for ctxt, id in taxonomy.contexts.items():

            if id not in taxonomy.contexts_used:
                continue

            entity = None
            scheme = None
            segments = {}
            period = None
            instant = None

            for dim in ctxt.get_dimensions():

                if dim[0] == "entity":
                    scheme = dim[1]
                    entity = dim[2]
                elif dim[0] == "segment":
                    segments[dim[1]] = dim[2]
                elif dim[0] == "period":
                    period = (dim[1], dim[2])
                elif dim[0] == "instant":
                    instant = dim[1]
                else:
                    raise RuntimeError("Should not happen in create_contexts")

            segs = []

            for k, v in segments.items():
                k2, v2 = taxonomy.lookup_segment(k, v)
                if k2 and v2:
                    segs.append(self.create_segment_member(k2, v2))

            crit = []
            if entity:
                crit.append(self.create_entity(entity, scheme, segs))

            if period:
                crit.append(self.create_period(period[0], period[1]))

            if instant:
                crit.append(self.create_instant(instant))

            ce = self.create_context(id, crit)

            self.resources.appendChild(ce)

    def make_div(self, par, elts):
        div = self.doc.createElement("div")
        self.add_elts(div, elts)
        par.appendChild(div)
        return div

    def add_elts(self, par, elts):
        for elt in elts:
            par.appendChild(elt)

    def make_text(self, t):
        return self.doc.createTextNode(t)

    def create_context(self, id, elts):
        ctxt = self.doc.createElement("xbrli:context")
        ctxt.setAttribute("id", id)
        for elt in elts:
            ctxt.appendChild(elt)
        return ctxt

    def create_entity(self, id, scheme, elts=None):

        if elts == None:
            elts = []

        ent = self.doc.createElement("xbrli:entity")
        cid = self.doc.createElement("xbrli:identifier")
        cid.setAttribute("scheme", scheme)
        cid.appendChild(self.doc.createTextNode(id))
        ent.appendChild(cid)

        for elt in elts:
            ent.appendChild(elt)

        return ent

    def create_instant(self, date):

        cperiod = self.doc.createElement("xbrli:period")

        instant = self.doc.createElement("xbrli:instant")
        instant.appendChild(self.doc.createTextNode(str(date)))
        cperiod.appendChild(instant)

        return cperiod

    def create_period(self, s, e):

        cperiod = self.doc.createElement("xbrli:period")

        start = self.doc.createElement("xbrli:startDate")
        start.appendChild(self.doc.createTextNode(str(s)))
        cperiod.appendChild(start)

        end = self.doc.createElement("xbrli:endDate")
        end.appendChild(self.doc.createTextNode(str(e)))
        cperiod.appendChild(end)

        return cperiod

    def create_segment_member(self, dim, value):

        seg = self.doc.createElement("xbrli:segment")

        expmem = self.doc.createElement("xbrldi:explicitMember")
        expmem.setAttribute("dimension", dim)
        expmem.appendChild(self.doc.createTextNode(value))
        seg.appendChild(expmem)

        return seg

    def create_metadata(self, taxonomy):

        metadata = taxonomy.get_document_metadata(self.data)

        for fact in metadata:
            if fact.name:
                fact.append(self.doc, self.hidden)
            
