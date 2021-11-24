
def get_class(kind):
    if kind == "gnucash":
        import gnucash_ixbrl.accounts_gnucash as a
        return a.Accounts
    elif kind == "piecash":
        import gnucash_ixbrl.accounts_piecash as a
        return a.Accounts
    else:
        raise RuntimeError("Accounts kind '%s' not known" % kind)

