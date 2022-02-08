
# Mapping taxonomy-free datums to facts so that iXBRL tagging can take place.
from . datum import *
from . fact import (
    StringFact, DateFact, MoneyFact, BoolFact, CountFact, NumberFact
)

from . period import Period
from . config import NoneValue
from . context import Context

from datetime import datetime

from lxml import objectify

xbrldi_ns = "http://xbrl.org/2006/xbrldi"

class NamedDimension:
    def describe(self, base):
        expmem = base.xbrldi_maker.explicitMember(self.value)
        expmem.set("dimension", self.dim)
        return expmem

class TypedDimension:
    def describe(self, base):

        # FIXME: Assumes single tag, containing single value

        try:
            # Get the namespace tag and look it up in the nsmap?
            nstag = self.content["tag"].split(":")[0]
            ns = base.nsmap[nstag]
            tag = self.content["tag"].split(":")[1]
        except Exception:
            raise RuntimeError(
                "Could not make sense of typed dimension tag %s" %
                self.content["tag"]
            )

        mkr = objectify.ElementMaker(
            annotate=False,
            namespace=ns,
        )

        elt = mkr(tag, self.value)

        mem = base.xbrldi_maker.typedMember()
        mem.set("dimension", self.dim)
        mem.append(elt)
        return mem

class Taxonomy:
    def __init__(self, cfg, data):
        self.cfg = cfg
        self.contexts = {}
        self.next_context_id = 0
        self.contexts_used = set()
        self.root_context = Context(None)

        self.decimals = data.get_config("metadata.accounting.decimals", 2)
        self.scale = data.get_config("metadata.accounting.scale", 0)
        self.currency = data.get_config(
            "metadata.accounting.currency", "EUR"
        )

        for defn in cfg.get("contexts"):
            ctxt = self.load_context(defn, data, self.contexts)
            self.contexts[defn.get("id")] = ctxt

        meta = {}
        for defn in cfg.get("metadata"):
            fact = self.load_metadata(data, defn, self.contexts)
            if fact:
                meta[defn.get("id")] = fact
        self.metadata = meta

    def get_context_id(self, ctxt):
        if ctxt in self.contexts:
            return self.contexts[ctxt]
        
        self.contexts[ctxt] = "ctxt-" + str(self.next_context_id)
        self.next_context_id += 1

        return self.contexts[ctxt]

    def create_fact(self, val):

        if isinstance(val, StringDatum):
            return self.create_string_fact(val)

        if isinstance(val, DateDatum):
            return self.create_date_fact(val)

        if isinstance(val, MoneyDatum):
            return self.create_money_fact(val)

        if isinstance(val, BoolDatum):
            return self.create_bool_fact(val)

        if isinstance(val, CountDatum):
            return self.create_count_fact(val)

        if isinstance(val, NumberDatum):
            return self.create_number_fact(val)

        if isinstance(val, VariableDatum):
            return self.get_metadata_by_id(val.value)

        raise RuntimeError("Not implemented: " + str(type(val)))

    def get_tag_name(self, id):
        key = "tags.{0}".format(id)
        return self.cfg.get(key, mandatory=False)

    def get_sign_reversed(self, id):
        key = "sign-reversed.{0}".format(id)
        return self.cfg.get_bool(key, False)

    def get_tag_dimensions(self, id):
        key = "segments.{0}".format(id)
        return self.cfg.get(key, mandatory=False)

    def get_description_tag_name(self, id):
        key = "description-tags.{0}".format(id)
        return self.cfg.get(key, mandatory=False)

    def create_description_fact(self, meta, desc, context):
        fact = StringFact(self.get_context_id(context),
                          self.get_description_tag_name(meta.id), desc)
        fact.dimensions = self.get_tag_dimensions(meta.id)
        self.observe_fact(fact)
        return fact

    def lookup_dimension(self, id, val):

        try:
            k1 = "segment.{0}.typed-dimension".format(
                id
            )
            k2 = "segment.{0}.content".format(id)
            dim = TypedDimension()
            dim.dim = self.cfg.get(k1)
            dim.content = self.cfg.get(k2)
            dim.value = val
            return dim
        except:
            pass

        k1 = "segment.{0}.dimension".format(id)
        k2 = "segment.{0}.map.{1}".format(id, val)
        dim = NamedDimension()
        dim.dim = self.cfg.get(k1)
        dim.value = self.cfg.get(k2)
        return dim

    def observe_fact(self, fact):
        # Keep track of which contexts are used.  Contexts which are
        # used by facts with no names don't need to be describe in the
        # output.
        if fact.name:
            self.contexts_used.add(fact.context)

    def create_money_fact(self, val):
        fact = MoneyFact(self.get_context_id(val.context),
                         self.get_tag_name(val.id), val.value,
                         self.currency,
                         self.scale,
                         self.decimals,
                         self.get_sign_reversed(val.id))
        fact.dimensions = self.get_tag_dimensions(val.id)
        self.observe_fact(fact)
        return fact

    def create_count_fact(self, val):
        fact = CountFact(self.get_context_id(val.context),
                         self.get_tag_name(val.id), val.value)
        fact.dimensions = self.get_tag_dimensions(val.id)
        self.observe_fact(fact)
        return fact

    def create_number_fact(self, val):
        fact = NumberFact(self.get_context_id(val.context),
                          self.get_tag_name(val.id), val.value)
        fact.dimensions = self.get_tag_dimensions(val.id)
        self.observe_fact(fact)
        return fact

    def create_string_fact(self, val):
        fact = StringFact(self.get_context_id(val.context),
                          self.get_tag_name(val.id), val.value)
        fact.dimensions = self.get_tag_dimensions(val.id)
        self.observe_fact(fact)
        return fact

    def create_bool_fact(self, val):
        fact = BoolFact(self.get_context_id(val.context),
                        self.get_tag_name(val.id), val.value)
        fact.dimensions = self.get_tag_dimensions(val.id)
        self.observe_fact(fact)
        return fact

    def create_date_fact(self, val):
        fact = DateFact(self.get_context_id(val.context),
                        self.get_tag_name(val.id), val.value)
        fact.dimensions = self.get_tag_dimensions(val.id)
        self.observe_fact(fact)
        return fact

    def create_context(self, cdef):

        key = cdef.get_key()

        if key in self.contexts:
            return self.contexts[key]

        ctxt = Context(self, cdef)
        ctxt.id = "ctxt-" + str(self.next_context_id)
        self.next_context_id += 1
        self.contexts[key] = ctxt
        return ctxt

    def get_namespaces(self):
        key = "namespaces"
        return self.cfg.get(key)

    def get_schemas(self):
        key = "schema"
        return self.cfg.get(key)

    def get_predefined_contexts(self):

        contexts = {}

        for defn in self.cfg.get("contexts"):
            id = defn.get("id")
            contexts[id] = self.contexts[id]

        return contexts

    def get_context(self, id):

        if id in self.contexts:
            return self.contexts[id]

        raise RuntimeError("No such context: %s" % id)

    def load_context(self, defn, data, contexts):

        ctxt = None

        if defn.get("from", mandatory=False):
            ctxt = contexts[defn.get("from")]
        else:
            ctxt = self.root_context

        if defn.get("entity", mandatory=False):
            scheme_def = defn.get("scheme")
            scheme = data.get_config(scheme_def, scheme_def)
            entity_def = defn.get("entity")
            entity = data.get_config(entity_def, entity_def)
            ctxt = ctxt.with_entity(scheme, entity)

        if defn.get("period", mandatory=False):
            period_def = defn.get("period")
            period = Period.load(data.get_config(period_def))
            ctxt = ctxt.with_period(period)

        if defn.get("instant", mandatory=False):
            instant_def = defn.get("instant")
            instant = data.get_config_date(instant_def)
            ctxt = ctxt.with_instant(instant)

        if defn.get("segments", mandatory=False):
            segments = defn.get("segments")

            if not isinstance(segments, list):
                raise RuntimeError(
                    "segments should be array of single item maps"
                )

            segs = []
            for elt in segments:
                if len(elt) != 1:
                    raise RuntimeError(
                        "segments should be array of single item maps"
                    )

                # Will only loop once
                for k, v in elt.items():
                    v = data.get_config(v, v)
                    segs.append((k, v))

            ctxt = ctxt.with_segments(segs)

        return ctxt

    def get_document_metadata(self, data):

        ctxts = self.get_predefined_contexts()

        ids = self.cfg.get("document-metadata")

        meta = []

        for id in ids:
            if id in self.metadata:
                meta.append(self.metadata[id])

        return meta

    def get_metadata_by_id(self, id):

        if id in self.metadata:
            return self.metadata[id]

        return NoneValue()

    def get_all_metadata(self, id):

        meta = [self.metadata[v] for v in self.metadata]
        return meta

    def load_metadata(self, data, defn, ctxts):

        id = defn.get("id")
        context = ctxts[defn.get("context")]

        if defn.get("config", mandatory=False):
            value_def = defn.get("config")
            value = data.get_config(value_def, mandatory=False)
        else:
            value = defn.get("value")

        # Missing values
        if isinstance(value, NoneValue):
            return NoneValue()

        kind = defn.get("kind", mandatory=False)
        if kind == "date":
            value = datetime.fromisoformat(value).date()
            datum = DateDatum(id, value, context)
        elif kind == "bool":
            value = bool(value)
            datum = BoolDatum(id, value, context)
        elif kind == "money":
            datum = MoneyDatum(id, value, context)
        elif kind == "count":
            datum = CountDatum(id, value, context)
        elif kind == "number":
            datum = NumberDatum(id, value, context)
        else:
            datum = StringDatum(id, value, context)
        fact = self.create_fact(datum)

        return fact

