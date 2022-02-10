
from . basic_element import BasicElement

class NoteHeading(BasicElement):

    counts = {}

    def __init__(self, id, level, title, data):

        super().__init__(id, data)
        self.level = level
        self.title = title

        self.headings = data.noteheadings

        self.num = self.headings.get_next(level)

        if id:
            data.set_note(id, str(self.format()))

    def format(self):
        if self.level == 1:
            return "%d" % self.num
        elif self.level == 2:
            return "%c" % chr(ord('a') + self.num - 1)
        else:
            raise RuntimeError("noteheading level can be 1 or 2")

    @staticmethod
    def load(elt_def, data):

        e = NoteHeading(
            elt_def.get("id", mandatory=False),
            elt_def.get("level", 1, mandatory=False),
            elt_def.get("title", mandatory=True),
            data
        )

        return e

    def to_text(self, taxonomy, out):
        txt = "%s. %s\n" % (self.format(), self.title)
        out.write(txt)

    def to_debug(self, taxonomy, out):
        txt = "%s. %s\n" % (self.format(), self.title)
        out.write(txt)

    def to_ixbrl_elt(self, par, taxonomy):

        txt = "%s. %s" % (self.format(), self.title)
        
        title = par.xhtml_maker("h" + str(self.level + 2), txt)
        title.set("class", "noteheading")
        title.set("id", self.id + "-noteheading")

        return [title]
