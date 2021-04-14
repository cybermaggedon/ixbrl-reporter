
from datetime import datetime

class Period:
    def __init__(self, name, s, e):
        self.name = name
        self.start = s
        self.end = e
    @staticmethod
    def load(cfg):
        return Period(
            cfg.get("name"),
            datetime.fromisoformat(cfg.get("start")).date(),
            datetime.fromisoformat(cfg.get("end")).date()
        )
    def __str__(self):
        return "{0} ({1}..{2})".format(self.name, self.start, self.end)
    def __repr__(self):
        return "Period({0},{1}..{2})".format(self.name, self.start, self.end)
    def days(self):
        diff = self.end - self.start
        return diff.days + 1
