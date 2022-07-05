
from . note_parse import *
from . layout import *

def expand_string(value, data):

    # This is template:, look up a note template and expand that
    if value.startswith("template:"):
        id = value[9:]
        tmpl = data.get_config("report.taxonomy.note-templates.%s" % id)
        return expand_string(tmpl, data)

    # If it's just a string, (no expand: or template: prefix) return a
    # StringElt
    if not value.startswith("expand:"):
        return StringElt(value, data)

    # The rest of this is the expand: case.

    value = value[7:]

    stack = []
    tkstack = []
    content = []

    exp = NoteParser.parse(value)
    for tk in exp:
        if isinstance(tk, TextToken):
            content.append(StringElt(tk.text, data))
        elif isinstance(tk, MetadataToken):
            content.append(
                MetadataElt(tk.name, tk.prefix, tk.suffix, tk.null, data)
            )
        elif isinstance(tk, ComputationToken):
            content.append(
                ComputationElt(tk.name, tk.period, data)
            )
        elif isinstance(tk, TagOpen):
            if tk.kind != "string":
                raise RuntimeError("Only string tags, currently")
            tkstack.append(tk)
            stack.append(content)
            content = []
        elif isinstance(tk, TagClose):
            ftk = tkstack[-1]
            tkstack.pop()
            elt = FactElt(ftk.name, ftk.context, {}, content, data)
            content = stack[-1]
            stack.pop()
            content.append(elt)
    
    return TagElt("span", {}, content, data)
