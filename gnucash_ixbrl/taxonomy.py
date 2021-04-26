
# Mapping taxonomy-free datums to facts so that iXBRL tagging can take place.
from . datum import (
    StringDatum, DateDatum, MoneyDatum, BoolDatum, CountDatum, NumberDatum
)
from . fact import (
    StringFact, DateFact, MoneyFact, BoolFact, CountFact, NumberFact
)

from . period import Period
from . config import NoneValue

from datetime import datetime

class Taxonomy:
    def __init__(self, cfg, name):
        self.cfg = cfg
        self.name = name
        self.contexts = {}
        self.next_context_id = 0
        self.contexts_used = set()

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

        raise RuntimeError("Not implemented: " + str(type(val)))

    def get_tag_name(self, id):
        key = "taxonomy.{0}.tags.{1}".format(self.name, id)
        return self.cfg.get(key, mandatory=False)

    def get_sign_reversed(self, id):
        key = "taxonomy.{0}.sign-reversed.{1}".format(self.name, id)
        return self.cfg.get_bool(key, False)

    def get_tag_dimensions(self, id):
        key = "taxonomy.{0}.segments.{1}".format(self.name, id)
        return self.cfg.get(key, mandatory=False)

    def lookup_segment(self, id, val):
        k1 = "taxonomy.{0}.segment.{1}.dimension".format(self.name, id)
        k2 = "taxonomy.{0}.segment.{1}.map.{2}".format(self.name, id, val)
        return self.cfg.get(k1), self.cfg.get(k2)

    def observe_fact(self, fact):
        # Keep track of which contexts are used.  Contexts which are
        # used by facts with no names don't need to be describe in the
        # output.
        if fact.name:
            self.contexts_used.add(fact.context)

    def create_money_fact(self, val):
        fact = MoneyFact(self.get_context_id(val.context),
                         self.get_tag_name(val.id), val.value,
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
        key = "taxonomy.{0}.namespaces".format(self.name)
        return self.cfg.get(key)

    def get_schemas(self):
        key = "taxonomy.{0}.schema".format(self.name)
        return self.cfg.get(key)

    def get_note(self, n):
        key = "taxonomy.{0}.notes.{1}".format(self.name, n)
        return self.cfg.get(key)

    def get_predefined_contexts(self, data):

        contexts = {}

        for defn in self.cfg.get("taxonomy.{0}.contexts".format(self.name)):

            ctxt = self.load_context(defn, data, contexts)
            contexts[defn.get("id")] = ctxt

        return contexts

    def get_context(self, id, data):

        contexts = self.get_predefined_contexts(data)

        if id in contexts: return contexts[id]

        raise RuntimeError("No such context: %s" % id)

    def load_context(self, defn, data, contexts):

        ctxt = None

        if defn.get("from", mandatory=False):
            ctxt = contexts[defn.get("from")]
        else:
            ctxt = data.get_root_context()

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

            for k, v in segments.items():
                v = data.get_config(v, v)
                segments[k] = v

            ctxt = ctxt.with_segments(segments)

        return ctxt

    def get_document_metadata(self, data):

        ctxts = self.get_predefined_contexts(data)

        ids = self.cfg.get("taxonomy.{0}.document-metadata".format(self.name))
        ids = set(ids)

        meta = []

        key = "taxonomy.{0}.metadata".format(self.name)
        for defn in self.cfg.get(key):

            if defn.get("id") in ids:

                fact = self.load_metadata(data, defn, ctxts)

                # Ignore missing
                if fact:
                    meta.append(fact)

        return meta

    def get_metadata_by_id(self, data, id):

        ctxts = self.get_predefined_contexts(data)

        key = "taxonomy.{0}.metadata".format(self.name)
        for defn in self.cfg.get(key):

            if defn.get("id") == id:

                return self.load_metadata(data, defn, ctxts)

        return NoneValue()

    def get_all_metadata(self, data, id):

        ctxts = self.get_predefined_contexts(data)

        meta = []

        key = "taxonomy.{0}.metadata".format(self.name)
        for defn in self.cfg.get(key):

            if defn.get("id") == id:
                fact = self.load_metadata(data, defn, ctxts)
                if fact:
                    meta.append(fact)

        return meta

    def get_all_metadata_by_id(self, data, id):

        ctxts = self.get_predefined_contexts(data)

        meta = []

        key = "taxonomy.{0}.metadata".format(self.name)
        for defn in self.cfg.get(key):

            if defn.get("id") == id:
                fact = self.load_metadata(data, defn, ctxts)
                if fact:
                    meta.append(fact)

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

