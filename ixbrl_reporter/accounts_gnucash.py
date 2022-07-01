
#
# Wrapper for GnuCash Python API, extracts account structure, splits, and
# also VAT return information from the accounts.
#
# Usage:
#     s = Accounts("file.gnucash")
#     rtn = s.get_vat()
#     print(rtn["totalVatDue"]["total"])
#     for v in rtn["totalVatDue"]["splits"]:
#         print(v["date"], v["amount"])

import gnucash
import json
import math

# Wrapper for GnuCash accounts.
class Accounts:

    # Opens a GnuCash book.  Config object provides configuration, needs
    # to support config.get("key.name") method.
    def __init__(self, file, rw=False):
        self.file = file
        self.session = None
        if rw:
            self.session = self.open_session(file)
        else:
            self.session = self.open_session_rw(file)
        self.book = self.session.book
        self.root = self.book.get_root_account()

    def __del__(self):
        if self.session != None:
            self.session.destroy()

    def save(self):
        self.session.save()

    # Creates a read-only session associated with a GnuCash file
    @staticmethod
    def open_session(file):
        mode = gnucash.SessionOpenMode.SESSION_READ_ONLY
        session = gnucash.Session(file, mode)
        return session

    @staticmethod
    def open_session_rw(file):
        mode = gnucash.SessionOpenMode.SESSION_NORMAL_OPEN
        session = gnucash.Session(file, mode)
        return session

    # Given a root account and start/end points return all matching splits
    # recorded against that account and any child accounts.
    def get_splits(self, acct, start, end, endinclusive=True):

        splits = []

        # Recurse into children
        childs = acct.get_children()
        if childs != None:
            for v in acct.get_children():
                splits.extend(self.get_splits(v, start, end))

        # Iterate over split list
        for spl in acct.GetSplitList():
            tx = spl.parent
            dt = tx.GetDate().date()

            inperiod=False

            if endinclusive and dt >= start and dt <= end:
                inperiod=True

            if (not endinclusive) and dt >= start and dt < end:
                inperiod=True

            if inperiod:
                splits.append(
                    {
                        "date": dt,
                        "amount": spl.GetAmount().to_double(),
                        "description": tx.GetDescription()
                    }
                )

        return splits

    # Return an account given an account locator.  Navigates through
    # hierarchy, account parts are colon separated.
    def get_account(self, par, locator):

        if par == None:
            acct = self.root
        else:
            acct = par

        for v in locator.split(":"):

            ch_acct = None

            for ch in acct.get_children():
                if ch.name == v:
                    ch_acct = ch
                    break

            if ch_acct == None:
                raise RuntimeError("Can't locate account '%s'" % locator)

            acct = ch_acct

        return acct

    def get_accounts(self, acct=None, pfx=""):

        if acct == None: acct = self.root

        ch = acct.get_children()
        if ch == None:
            return []
        
        res = []

        for v in acct.get_children():
            res.append(pfx + v.name)
            res.extend(
                self.get_accounts(v, pfx + v.name + ":")
            )
        return res

    def is_debit(self, accts):
        tp = accts.GetType()
        if tp == gnucash.ACCT_TYPE_INCOME: return True
        if tp == gnucash.ACCT_TYPE_EQUITY: return True
        if tp == gnucash.ACCT_TYPE_EXPENSE: return True
        return False

    # Get vendor by vendor ID, returns Vendor object
    def get_vendor(self, id):
        return self.book.VendorLookupByID(id)

    # Get list of all vendors, list of Vendor objects
    def get_vendors(self):

        query = gnucash.Query()
        query.search_for('gncVendor')
        query.set_book(self.book)
        vendors = []

        vnds = [
            gnucash.gnucash_business.Vendor(instance=result)
            for result in query.run()
        ]

        query.destroy()

        return vnds

    # Create a vendor
    def create_vendor(self, id, currency, name):
        return gnucash.gnucash_business.Vendor(self.book, id, currency, name)

    # Get a currency given the mnemonic.  Returns a Commodity object.
    def get_currency(self, mn):
        return self.book.get_table().lookup("CURRENCY", mn)

    # Get next bill ID given vendor
    def next_bill_id(self, vendor):
        return self.book.BillNextID(vendor)

    # Createa a bill
    def create_bill(self, id, currency, vendor, date_opened):
        return gnucash.gnucash_business.Bill(self.book, id, currency, vendor,
                                             date_opened)

    # Add a bill entry to a bill
    def create_bill_entry(self, bill, date_opened, description,
                          liability_acct, quantity, price):
        ent = gnucash.gnucash_business.Entry(self.book, bill, date_opened)
        ent.SetDescription(description)
        ent.SetBillAccount(liability_acct)
        ent.SetQuantity(gnucash.GncNumeric(quantity))
        ent.SetBillPrice(gnucash.GncNumeric(round(100 * price), 100))
        return ent
