
# Note markup parser.

class TextToken:
    def __init__(self, text):
        self.text = text

class TagOpen:
    def __init__(self, name, context=None, kind="string"):
        self.name = name
        self.context = context
        self.kind = kind

class TagClose:
    def __init__(self, name):
        self.name = name

class MetadataToken:
    def __init__(self, name, prefix="", suffix="", null=""):
        self.name = name
        self.prefix = prefix
        self.suffix = suffix
        self.null = null

class ComputationToken:
    def __init__(self, name, context="", period=""):
        self.name = name
        self.context = context
        self.period = period

class NoteParser:
    @staticmethod
    def parse(note):

        tokens = []

        stack = []

        IN_TEXT = 1
        POST_TILDE = 2
        IN_TAG_NAME = 3
        IN_COMPUTATION_NAME = 4
        IN_METADATA_NAME = 5

        state = IN_TEXT

        text = ""

        for c in note:

            if state == IN_TEXT:

                if c == '~':
                    if text != "":
                        tokens.append(TextToken(text))
                    state = POST_TILDE
                    continue

                if c == '}':
                    if text != "":
                        tokens.append(TextToken(text))
                    tokens.append(TagClose(stack.pop().name))
                    state = IN_TEXT
                    text = ""
                    continue

                text += c
                continue

            if state == POST_TILDE:

                if c == '{':
                    state = IN_TAG_NAME
                    tag_name = ""
                    continue

                if c == '[':
                    state = IN_METADATA_NAME
                    metadata_name = ""
                    continue

                if c == '(':
                    state = IN_COMPUTATION_NAME
                    computation_name = ""
                    continue

                err = "Didn't expect character '%c' after a tilde" % c
                raise RuntimeError(err)

            if state == IN_TAG_NAME:

                if c == '=':

                    toks = tag_name.split(":")

                    if len(toks) == 0:
                        raise RuntimeError("Empty tag name")

                    if len(toks) > 2:
                        raise RuntimeError(
                            "Too many parts to tag name: %s" % tag_name
                        )

                    if len(toks) > 2:
                        if toks[2] == "m":
                            toks[2] = "money"
                        elif toks[2] == "s":
                            toks[2] = "string"
                        elif toks[2] == "c":
                            toks[2] = "count"
                        elif toks[2] == "b":
                            toks[2] = "bool"
                        elif toks[2] == "n":
                            toks[2] = "number"
                        elif toks[2] == "s":
                            toks[2] = "string"

                    tag = TagOpen(*toks)

                    tokens.append(tag)
                    stack.append(tag)

                    state = IN_TEXT
                    text = ""

                    continue

                tag_name += c
                continue

            if state == IN_METADATA_NAME:
                if c == ']':

                    toks = metadata_name.split(":")

                    if len(toks) < 1 or len(toks) > 4:
                        raise RuntimeError(
                            "Too many fields: %s" % metadata_name
                        )
                    tok = MetadataToken(*toks)

                    tokens.append(tok)
                    text = ""
                    state = IN_TEXT
                    continue

                metadata_name += c
                continue

            if state == IN_COMPUTATION_NAME:
                if c == ')':

                    toks = computation_name.split(":")

                    if len(toks) < 1 or len(toks) > 3:
                        raise RuntimeError(
                            "Too many fields: %s" % computation_name
                        )
                    tok = ComputationToken(*toks)

                    tokens.append(tok)
                    text = ""
                    state = IN_TEXT
                    continue

                computation_name += c
                continue

        if state == IN_TEXT:
            if text != "":
                tokens.append(TextToken(text))
        else:
            raise RuntimeError("Unbalanced note, in state %d" % state)

        return tokens

