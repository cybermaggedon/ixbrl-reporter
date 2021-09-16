
# A title element forms the title page of a report.  The taxonomy support keeps
# the title page taxonomy-free, but this code still contains a set of hard-coded
# fields which make up a report.

from . basicelement import BasicElement
from . fact import *

import base64

class Title(BasicElement):
    def __init__(self, id, img, type, data):
        super().__init__(id, data)
        self.title = data.get_config("metadata.report.title")
        self.date = data.get_config("metadata.report.date")
        self.img = img
        self.type = type

    @staticmethod
    def load(elt_def, data):

        e = Title(
            elt_def.get("id"),
            elt_def.get("signature-image"),
            elt_def.get("signature-type"),
            data
        )

        return e

    def to_text(self, out):
        return

    def to_ixbrl_elt(self, par, taxonomy):

        div = par.xhtml_maker.div({
            "class": "title page",
            "id": self.id + "-element",
        })

        def add_company_name(fact):
            div2 = par.xhtml_maker.h1()
            div2.set("class", "heading")
            div2.append(fact.to_elt(par))
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "company-name").use(
            add_company_name
        )
        
        def add_report_title(fact):
            div2 = par.xhtml_maker.div()
            div2.set("class", "subheading")
            div2.append(fact.to_elt(par))
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "report-title").use(
            add_report_title
        )

        def add_company_number(fact):
            div2 = par.xhtml_maker.div("Registered number: ", {
                "class": "information"
            })
            div2.append(fact.to_elt(par))
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "company-number").use(
            add_company_number
        )

        div2 = par.xhtml_maker.div({"class": "information"}, "For the period: ")
        taxonomy.get_metadata_by_id(self.data, "period-start").use(
            lambda fact: div2.append(fact.to_elt(par))
        )
        div2.append(par.xhtml_maker.span(" to "))
        taxonomy.get_metadata_by_id(self.data, "period-end").use(
            lambda fact: div2.append(fact.to_elt(par))
        )

        def add_report_date(fact):
            div2 = par.xhtml_maker.div({"class": "information"}, "Date: ")
            div2.append(fact.to_elt(par))
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "report-date").use(
            add_report_date
        )

        div2 = par.xhtml_maker.div({"class": "information"}, "Directors: ")
        div.append(div2)

        meta = taxonomy.get_all_metadata_by_id(self.data, "officer")

        for i in range(0, len(meta)):
            if i > 0:
                div2.append(par.xhtml_maker.span(", "))
            div2.append(meta[i].to_elt(par))

        div2.append(par.xhtml_maker.span("."))

        sig = par.xhtml_maker.div({"class": "signature"})
        div.append(sig)

        p = par.xhtml_maker.p()
        sig.append(p)

        p.append(par.xhtml_maker.span(
            "Approved by the board of directors and authorised for "
            "publication on "
        ))

        taxonomy.get_metadata_by_id(self.data, "authorised-date").use(
            lambda fact: p.append(fact.to_elt(par))
        )

        p.append(par.xhtml_maker.span("."))
        sig.append(p)

        p = par.xhtml_maker.p()

        p.append(par.xhtml_maker.span(
            "Signed on behalf of the directors by "
        ))

        taxonomy.get_metadata_by_id(self.data, "signing-officer").use(
            lambda fact: p.append(fact.to_elt(par))
        )

        p.append(par.xhtml_maker.span(
            self.data.get_config("metadata.report.signed-by")
        ))

        p.append(par.xhtml_maker.span("."))

        sig.append(p)

        if self.img and self.type:
            img = par.xhtml_maker.img()
            img.set("alt", "Director's signature")
            data = base64.b64encode(open(self.img, "rb").read()).decode("utf-8")
            img.set("src",
                             "data:{0};base64,{1}".format(self.type, data)
                             )
            sig.append(img)

        div.append(sig)
        
        return div
