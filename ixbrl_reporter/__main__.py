import sys

from ixbrl_reporter.config import Config
import ixbrl_reporter.accounts as accounts
from ixbrl_reporter.taxonomy import Taxonomy
from ixbrl_reporter.data_source import DataSource

if __name__ == "__main__":

    if len(sys.argv) < 4:
        sys.stderr.write("Usage:\n")
        sys.stderr.write("\tixbrl-reporter <config> <report> <format>\n")
        sys.exit(1)

    try:

        cfg = Config.load(sys.argv[1])
        cfg.set("internal.software-name", "ixbrl-reporter")
        cfg.set("internal.software-version", "1.0.4")

        kind = cfg.get("accounts.kind")
        file = cfg.get("accounts.file")

        cls = accounts.get_class(kind)
        session = cls(file)

        d = DataSource(cfg, session)

        elt = d.get_element(sys.argv[2])

        if sys.argv[3] == "ixbrl":
            tx_cfg = cfg.get("report.taxonomy")
            tx = Taxonomy(tx_cfg, d)
            elt.to_ixbrl(tx, sys.stdout)
        elif sys.argv[3] == "html":
            tx_cfg = cfg.get("report.taxonomy")
            tx = Taxonomy(tx_cfg, d)
            elt.to_html(tx, sys.stdout)
        elif sys.argv[3] == "text":
            tx_cfg = cfg.get("report.taxonomy")
            tx = Taxonomy(tx_cfg, d)
            elt.to_text(tx, sys.stdout)
        elif sys.argv[3] == "debug":
            tx_cfg = cfg.get("report.taxonomy")
            tx = Taxonomy(tx_cfg, d)
            elt.to_debug(tx, sys.stdout)
        else:
            raise RuntimeError("Output type '%s' not known." % sys.argv[3])

    except Exception as e:
        sys.stderr.write("Exception: %s\n" % str(e))
        raise e
        sys.exit(1)

