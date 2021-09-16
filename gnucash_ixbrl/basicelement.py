
# Base class for elements.  Any element can be output as an iXBRL document.
# There is code here which handles the standard 'outer' iXBRL document
# and global context management.
from . period import Period
from . fact import *

xhtml_ns = "http://www.w3.org/1999/xhtml"
ix_ns = "http://www.xbrl.org/2013/inlineXBRL"
xlink_ns = "http://www.w3.org/1999/xlink"
link_ns = "http://www.xbrl.org/2003/linkbase"
xbrli_ns = "http://www.xbrl.org/2003/instance"
xbrldi_ns = "http://xbrl.org/2006/xbrldi"

from lxml import objectify, etree

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
  padding: 1rem;
}

.header {
  font-weight: bold;
  margin-top: 1rem;
}

.label {
  clear: left;
  float: left;
  width: 20rem;
}

.label.breakdown.header {
  margin-bottom: 0.2rem;
}

.value {
  font-family: Source Code Pro, monospace;
  font-size: 10pt;
  float: left;
  width: 10rem;
  padding-left: 1rem;
  padding-right: 1rem;
  margin-right: 1rem;
}

@media print {
  .value {
    font-family: Source Code Pro, monospace;
    font-size: 1rem;
    width: 18%;
  }
  * {
    font-size: 1rem;
  }
  .label {
    width: 40%; 
  }
  .periodname {
    width: 18%;
  }
  .currency {
    width: 18%;
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
  text-align: center;
  float: left;
  width: 10rem;
  margin-right: 1rem;
}

.currency {
  text-align: right;
  padding-left: 1em;
  padding-right: 1em;
  float: left;
  width: 10rem;
  margin-right: 1rem;
  margin-top: 0.25em;
}

.period.value {
  text-align: right;
}

.period.value.negative {
  padding-left: 2rem;
  padding-right: 0rem;
//  position: relative;
//  left: 1rem;
  color: #400000;
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
  margin: 0rem 0rem 0rem 1rem;
  padding: 4px;
}

.fact .ref {
  width: 5em;
  text-align: center;
  color: white;
  background-color: #2ca469;
  border: 2px solid #104020;
  font-weight: bold;
  font-size: small;
  padding-left: 0.1rem;
  padding-right: 0.1rem;
}

.fact .description {
  width: 22em;
  font-size: small;
}

.fact .value {
  border: 2px solid black;
  background-color: white;
}

.fact .value.false {
  color: #a0a0a0;
}
        """

        elt.append(
            self.xhtml_maker.style(style_text)
        )

        elt.style.set("type", "text/css")

    def to_html(self, taxonomy, out):

        nsmap={
            None: xhtml_ns,
        }

        self.nsmap = nsmap

        self.add_makers(self.nsmap)

        self.html = self.xhtml_maker.html(
            self.xhtml_maker.head(),
            self.xhtml_maker.body(
                self.xhtml_maker.div(
                    {"class": "hidden"},
                    self.ix_maker.header(
                        self.ix_maker.hidden(),
                        self.ix_maker.references(),
                        self.ix_maker.resources(),
                    ),
                ),
            ),
        )

        def add_title(val):
            self.html.head.append(
                self.xhtml_maker.title(val)
            )

        self.data.get_config("metadata.report.title").use(add_title)

        self.add_style(self.html.head)

        header_op = objectify.ObjectPath(".body.div.{%s}header" % (
            ix_ns
        ))

        self.header = header_op(self.html)

        elt = self.to_ixbrl_elt(self, taxonomy)

        # Deep copies the tree, converts all the ix: elements to span elements
        def walk(elt, level=0):
            ns = elt.nsmap[elt.prefix]
            if ns == ix_ns:
                elt2 = self.xhtml_maker.span(elt.text)
            else:
                elt2 = self.xhtml_maker(elt.tag, elt.text)
                for k in elt.keys():
                    elt2.set(k, elt.attrib[k])
            for v in elt.iterchildren():
                elt2.append(walk(v, level + 1))
            return elt2
        elt = walk(elt)

        self.html.body.append(elt)

        # Last remains of the ix: namespace are the header.  Just delete
        # the hidden div
        h = self.header
        hiddiv = h.getparent()
        hiddiv.getparent().remove(hiddiv)

        if self.data.get_config_bool("metadata.report.pretty-print",
                                     mandatory=False):
            out.write(etree.tostring(
                self.html, pretty_print=True, xml_declaration=True
            ).decode("utf-8"))
        else:
            out.write(etree.tostring(
                self.html, xml_declaration=True
            ).decode("utf-8"))

        return

    def add_makers(self, nsmap):

        xhtml_maker = objectify.ElementMaker(
            annotate=False,
            namespace=xhtml_ns,
            nsmap=nsmap,
        )

        self.xhtml_maker = xhtml_maker

        self.ix_maker = objectify.ElementMaker(
            annotate=False,
            namespace=ix_ns,
        )

        self.xlink_maker = objectify.ElementMaker(
            annotate=False,
            namespace=xlink_ns,
        )

        self.link_maker = objectify.ElementMaker(
            annotate=False,
            namespace=link_ns,
        )

        self.xbrli_maker = objectify.ElementMaker(
            annotate=False,
            namespace=xbrli_ns,
        )

        self.xbrldi_maker = objectify.ElementMaker(
            annotate=False,
            namespace=xbrldi_ns,
        )

    def to_ixbrl(self, taxonomy, out):

        nsmap={
            None: xhtml_ns,
            "ix": ix_ns,
            "link": link_ns,
            "xlink": xlink_ns,
            "xbrli": xbrli_ns,
            "xbrldi": xbrldi_ns,
            "ixt2":
            "http://www.xbrl.org/inlineXBRL/transformation/2011-07-31",
            "iso4217": "http://www.xbrl.org/2003/iso4217",
        }

        ns = taxonomy.get_namespaces()
        for k in ns:
            nsmap[k] = ns[k]

        self.nsmap = nsmap

        self.add_makers(self.nsmap)

        self.html = self.xhtml_maker.html(
            self.xhtml_maker.head(),
            self.xhtml_maker.body(
                self.xhtml_maker.div(
                    {"class": "hidden"},
                    self.ix_maker.header(
                        self.ix_maker.hidden(),
                        self.ix_maker.references(),
                        self.ix_maker.resources(),
                    ),
                ),
            ),
        )

        def add_title(val):
            self.html.head.append(
                self.xhtml_maker.title(val)
            )

        self.data.get_config("metadata.report.title").use(add_title)

        self.add_style(self.html.head)

        header_op = objectify.ObjectPath(".body.div.{%s}header" % (
            ix_ns
        ))

        self.header = header_op(self.html)

        # This creates some contexts, hence do this first.
        self.create_metadata(self.ix_maker, taxonomy)

        schemas = taxonomy.get_schemas()
        for url in schemas:
            schema = self.link_maker.schemaRef("")
            schema.set("{%s}type" % xlink_ns, "simple")
            schema.set("{%s}href" % xlink_ns, url)
            self.header.references.append(schema)

        elt = self.to_ixbrl_elt(self, taxonomy)
        self.html.body.append(elt)

        # Contexts get created above, hence do this last.
        self.create_contexts(taxonomy)

        currency = self.data.get_config("metadata.report.currency")

        unit = self.xbrli_maker.unit(
            {"id": currency},
            self.xbrli_maker.measure("iso4217:" + currency)
        )
        self.header.resources.append(unit)

        unit = self.xbrli_maker.unit(
            {"id": "pure"},
            self.xbrli_maker.measure("xbrli:pure")
        )
        self.header.resources.append(unit)

        if self.data.get_config_bool("metadata.report.pretty-print",
                                     mandatory=False):
            out.write(etree.tostring(
                self.html, pretty_print=True, xml_declaration=True
            ).decode("utf-8"))
        else:
            out.write(etree.tostring(
                self.html, xml_declaration=True
            ).decode("utf-8"))

        return

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

            if len(segments) == 0:
                segs = []
            else:
                segs = [
                    self.xbrli_maker.segment()
                ]
                for k, v in segments.items():
                    dim = taxonomy.lookup_dimension(k, v)
                    if dim:
                        segs[0].append(dim.describe(self))

            crit = []
            if entity:
                crit.append(self.create_entity(entity, scheme, segs))

            if period:
                crit.append(self.create_period(period[0], period[1]))

            if instant:
                crit.append(self.create_instant(instant))

            ce = self.create_context(id, crit)

            self.header.resources.append(ce)

    def create_context(self, id, elts):

        ctxt = self.xbrli_maker.context({"id": id})

        for elt in elts:
            ctxt.append(elt)

        return ctxt

    def create_entity(self, id, scheme, elts=None):

        if elts == None:
            elts = []

        ent = self.xbrli_maker.entity(
            self.xbrli_maker.identifier({
                "scheme": scheme
            }),
        )

        for elt in elts:
            ent.append(elt)

        return ent

    def create_instant(self, date):

        cperiod = self.xbrli_maker.period(
            self.xbrli_maker.instant(str(date))
        )

        return cperiod

    def create_period(self, s, e):

        cperiod = self.xbrli_maker.period(
            self.xbrli_maker.startDate(str(s)),
            self.xbrli_maker.endDate(str(e))
        )

        return cperiod

    def create_segment_member(self, dim, value):

        expmem = self.xbrli_maker.explicitMember(value)
        expmem.set("dimension", dim)
        return expmem

    def create_metadata(self, maker, taxonomy):

        metadata = taxonomy.get_document_metadata(self.data)

        for fact in metadata:
            if fact.name:
                self.header.hidden.append(fact.to_elt(self))
            
