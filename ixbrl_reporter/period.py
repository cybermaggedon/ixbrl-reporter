
# A period of time.  Periods have a name, start and end date.  The convention
# used in ixbrl-reporter is that periods are bounded by dates inclusively.
# i.e. an event which occurs on the end date is *included in* the period.
from datetime import datetime

class Period:
    def __init__(self, name, s, e):
        self.name = name
        self.start = s
        self.end = e
    @staticmethod
    def load(cfg):
        try:
            return Period(
                cfg.get("name"),
                datetime.fromisoformat(cfg.get("start")).date(),
                datetime.fromisoformat(cfg.get("end")).date()
            )
        except:
            raise RuntimeError("Could not parse %s" % str(cfg))
    def __str__(self):
        return "{0} ({1}..{2})".format(self.name, self.start, self.end)
    def __repr__(self):
        return "Period({0},{1}..{2})".format(self.name, self.start, self.end)
    def days(self):
        diff = self.end - self.start
        return diff.days + 1
