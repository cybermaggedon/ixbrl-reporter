
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
from . computation import create_uuid

class BasicElement:

    def __init__(self, id, data):
        if id:
            self.id = id
        else:
            self.id = "elt-" + create_uuid()
        self.data = data

    def add_style(self, elt):

        style_text = self.data.get_config("report.style")

        elt.append(
            self.xhtml_maker.style(style_text)
        )

        elt.style.set("type", "text/css")

    def to_html(self, taxonomy, out):

        # Make the HTML by removing the iXBRL stuff from the iXBRL document.

        # Get the iXBRL doc.
        html = self.to_ixbrl_tree(taxonomy)

        # Deep copies the tree, converts all the ix: elements to span elements
        def walk(elt, level=0):
            ns = elt.nsmap[elt.prefix]

            if ns == ix_ns:

                if elt.tag == "{%s}header" % ix_ns:
                    return self.xhtml_maker.span("")

                elt2 = self.xhtml_maker.span(elt.text)

            else:
                elt2 = self.xhtml_maker(elt.tag, elt.text)
                for k in elt.keys():
                    elt2.set(k, elt.attrib[k])
            for v in elt.iterchildren():
                elt2.append(walk(v, level + 1))
            return elt2

        # Remove ix elements.
        html = walk(html)
    
        if self.data.get_config_bool("pretty-print",
                                     mandatory=False):
            out.write(etree.tostring(
                html, pretty_print=True, xml_declaration=True
            ).decode("utf-8"))
        else:
            out.write(etree.tostring(
                html, xml_declaration=True
            ).decode("utf-8"))

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

    def init_html(self, taxonomy):

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
        
    def to_ixbrl_tree(self, taxonomy):

        self.init_html(taxonomy)

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

        self.data.get_config("report.title").use(add_title)

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

        report = self.xhtml_maker.div({"id": "report", "class": "report"})
        self.html.body.append(report)

        elts = self.to_ixbrl_elt(self, taxonomy)
        for elt in elts:
            report.append(elt)

        # Contexts get created above, hence do this last.
        self.create_contexts(taxonomy)

        currency = self.data.get_config("metadata.accounting.currency")

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

        return self.html

    def to_ixbrl(self, taxonomy, out):

        html = self.to_ixbrl_tree(taxonomy)

        if self.data.get_config_bool("pretty-print",
                                     mandatory=False):
            out.write(etree.tostring(
                html, pretty_print=True, xml_declaration=True
            ).decode("utf-8"))
        else:
            out.write(etree.tostring(
                html, xml_declaration=True
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
            },
            id
            )
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
            
