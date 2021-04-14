
from . multi_period import MultiPeriodWorksheet
from . computation import Computable, get_computations

def get_worksheet(id, cfg):

    comps = get_computations(cfg)

    for ws_def in cfg.get("worksheets"):

        if ws_def.get("id") == id:

            kind = ws_def.get("kind")

            if kind == "multi-period":
                return MultiPeriodWorksheet.create(cfg, ws_def, comps, session)

            raise RuntimeError("Don't know worksheet type '%s'" % kind)

    raise RuntimeError("Could not find worksheet '%s'" % id)

