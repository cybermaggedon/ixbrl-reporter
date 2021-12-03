
def get_class(kind):
    if kind == "gnucash":
        import ixbrl_reporter.accounts_gnucash as a
        return a.Accounts
    elif kind == "piecash":
        import ixbrl_reporter.accounts_piecash as a
        return a.Accounts
    elif kind == "csv":
        import ixbrl_reporter.accounts_csv as a
        return a.Accounts
    else:
        raise RuntimeError("Accounts kind '%s' not known" % kind)

