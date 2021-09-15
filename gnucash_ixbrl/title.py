
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

        div = par.maker.div({
            "class": "title page",
            "id": self.id + "-element",
        })

        def add_company_name(fact):
            div2 = par.maker.h1()
            div2.set("class", "heading")
            fact.append(par.maker, div2)
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "company-name").use(
            add_company_name
        )
        
        def add_report_title(fact):
            div2 = par.maker.div()
            div2.set("class", "subheading")
            fact.append(par.maker, div2)
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "report-title").use(
            add_report_title
        )

        def add_company_number(fact):
            div2 = par.maker.div("Registered number: ", {
                "class": "information"
            })
            fact.append(par.maker, div2)
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "company-number").use(
            add_company_number
        )

        div2 = par.maker.div({"class": "information"}, "For the period: ")
        taxonomy.get_metadata_by_id(self.data, "period-start").use(
            lambda fact: fact.append(par.maker, div2)
        )
        div2.append(objectify.StringElement(" to "))
        taxonomy.get_metadata_by_id(self.data, "period-end").use(
            lambda fact: fact.append(par.maker, div2)
        )

        def add_report_date(fact):
            div2 = par.maker.div({"class": "information"}, "Date: ")
            fact.append(par.maker, div2)
            div.append(div2)

        taxonomy.get_metadata_by_id(self.data, "report-date").use(
            add_report_date
        )

        div.append(par.maker.div({"class": "information"}, "Directors: "))

        meta = taxonomy.get_all_metadata_by_id(self.data, "officer")

        for i in range(0, len(meta)):
            if i > 0:
                div2.append(objectify.StringElement(", "))
            meta[i].append(par.maker, div2)

        div2.append(objectify.StringElement("."))

        sig = par.maker.div({"class": "signature"})
        div.append(sig)

        p = par.maker.p()
        sig.append(p)

        p.append(objectify.StringElement(
            "Approved by the board of directors and authorised for "
            "publication on "
        ))

        taxonomy.get_metadata_by_id(self.data, "authorised-date").use(
            lambda fact: fact.append(par.maker, p)
        )

        p.append(objectify.StringElement("."))
        sig.append(p)

        p = par.maker.p()

        p.append(objectify.StringElement(
            "Signed on behalf of the directors by "
        ))

        taxonomy.get_metadata_by_id(self.data, "signing-officer").use(
            lambda fact: fact.append(par.maker, p)
        )

        p.append(objectify.StringElement(
            self.data.get_config("metadata.report.signed-by")
        ))

        p.append(objectify.StringElement("."))

        sig.append(p)

        if self.img and self.type:
            img = par.maker.img()
            img.set("alt", "Director's signature")
            data = base64.b64encode(open(self.img, "rb").read()).decode("utf-8")
            img.set("src",
                             "data:{0};base64,{1}".format(self.type, data)
                             )
            sig.append(img)

        div.append(sig)
        
        return div
