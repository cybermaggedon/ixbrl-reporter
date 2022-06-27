
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

import piecash
import json
import math

# Wrapper for GnuCash accounts.
class Accounts:

    # Opens a GnuCash book.  Config object provides configuration, needs
    # to support config.get("key.name") method.
    def __init__(self, file, rw=False):
        self.book = piecash.open_book(file, readonly=not rw)

    def __del__(self):
        pass

    def save(self):
        pass
        # self.session.save()

    # Given a root account and start/end points return all matching splits
    # recorded against that account and any child accounts.
    def get_splits(self, acct, start, end, endinclusive=True):

        splits = []

        # Recurse into children
        childs = acct.children
        if childs != []:
            for v in childs:
                splits.extend(self.get_splits(v, start, end))

        # Iterate over split list
        for spl in acct.splits:
            tx = spl.transaction
            dt = tx.post_date

            inperiod = False

            if endinclusive and dt >= start and dt <= end:
                inperiod = True

            if (not endinclusive) and dt >= start and dt < end:
                inperiod = True

            if inperiod:
                splits.append(
                    {
                        "date": dt,
                        "amount": float(spl.quantity),
                        "description": tx.description
                    }
                )

        return splits

    # Return an account given an account locator.  Navigates through
    # hierarchy, account parts are colon separated.
    def get_account(self, par, locator):

        if par == None: par = self.book.root_account

        acct = par

        for v in locator.split(":"):
            acct = acct.children(name=v)
            if acct == None:
                raise RuntimeError("Can't locate account '%s'" % locator)
        return acct

    def get_accounts(self, acct=None, pfx=""):

        if acct == None: acct = self.book.root_account

        ch = acct.children
        if ch == None:
            return []
        
        res = []

        for v in acct.children:
            res.append(pfx + v.name)
            res.extend(
                self.get_accounts(v, pfx + v.name + ":")
            )
        return res

    def is_debit(self, acct):
        if acct.type == "INCOME": return True
        if acct.type == "EQUITY": return True
        if acct.type == "EXPENSE": return True
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
    def create_bill_entry(self, bill, date_opened):
        entry = gnucash.gnucash_business.Entry(self.book, bill, date_opened)
        return entry

    # Get our 'special' predefined vendor for VAT returns.
    def get_vat_vendor(self):

        id = "hmrc-vat"

        # If vendor does not exist, create it
        vendor = self.get_vendor(id)
        if vendor == None:

            gbp = self.get_currency("GBP")
            name = "HM Revenue and Customs - VAT"
            vendor = self.create_vendor(id, gbp, name)

            address = vendor.GetAddr()
            address.SetName("VAT Written Enquiries")
            address.SetAddr1("123 St Vincent Street")
            address.SetAddr2("Glasgow City")
            address.SetAddr3("Glasgow G2 5EA")
            address.SetAddr4("UK")

            self.save()

        return vendor

    # Post the VAT bill to a liability account.
    def post_vat_bill(self, billing_id, bill_date, due_date, vat, notes, memo):

        # Get the VAT vendor (HMRC)
        vendor = self.get_vat_vendor()

        bill_id  = self.next_bill_id(vendor)
        bill = self.create_bill(bill_id, vendor.GetCurrency(), vendor,
                                bill_date)

        vat_due = vat.totalVatDue
        vat_rebate = vat.vatReclaimedCurrPeriod
        bill.SetNotes(notes)
        bill.SetBillingID(billing_id)

        liability_account_name = self.config.get("accounts.liabilities")
        liability_acct = self.get_account(
            self.book.root_account, liability_account_name
        )

        bill_account_name = self.config.get("accounts.bills")
        bill_acct = self.get_account(
            self.book.root_account, bill_account_name
        )

        description = "VAT from sales and acquisitions"
        ent = self.create_bill_entry(bill, bill_date)
        ent.SetDescription(description)
        ent.SetBillAccount(liability_acct)
        ent.SetQuantity(gnucash.GncNumeric(1.0))
        ent.SetBillPrice(gnucash.GncNumeric(round(100 * vat_due), 100))

        description = "VAT rebate on acquisitions"
        ent = self.create_bill_entry(bill, bill_date)
        ent.SetDescription(description)
        ent.SetBillAccount(liability_acct)
        ent.SetQuantity(gnucash.GncNumeric(1.0))
        ent.SetBillPrice(gnucash.GncNumeric(-round(100 * vat_rebate), 100))

        bill.PostToAccount(bill_acct, bill_date, due_date, memo, False, False)

        self.save()

