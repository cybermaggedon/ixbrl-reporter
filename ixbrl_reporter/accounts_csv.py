
import csv
import datetime

# Wrapper for CSV accounts.
class Accounts:

    # Opens a CSV file.  Config object provides configuration, needs
    # to support config.get("key.name") method.
    def __init__(self, file):

        self.transactions = []
        tx = {}

        with open(file) as f:

            c = csv.DictReader(f)
            for row in c:

                if row["Date"] != "":

                    if tx: self.transactions.append(tx)

                    dt = row["Date"]
                    dt = datetime.datetime.strptime(dt, "%d/%m/%y").date()

                    tx = {
                        "id": row["Transaction ID"],
                        "description": row["Description"],
                        "date": dt,
                        "splits": {}
                    }

                acct = row["Full Account Name"]
                amt = row["Amount Num."]
                amt = amt.replace(",", "")

                tx["splits"][acct] = float(amt)

        if tx: self.transactions.append(tx)

    def __del__(self):
        pass

    def save(self):
        pass

    # Given a root account and start/end points return all matching splits
    # recorded against that account and any child accounts.
    def get_splits(self, acct, start, end, endinclusive=True):

        splits = []

        for tx in self.transactions:

            for ac in tx["splits"]:

                if ac.startswith(acct):

                    dt = tx["date"]

                    inperiod = False

                    if endinclusive and dt >= start and dt <= end:
                        inperiod = True

                    if (not endinclusive) and dt >= start and dt < end:
                        inperiod = True

                    if inperiod:
                        splits.append({
                            "date": dt,
                            "amount": tx["splits"][ac],
                            "description": tx["description"]
                        })

        return splits

    # Return an account given an account locator.  Navigates through
    # hierarchy, account parts are colon separated.
    def get_account(self, par, locator):

        if par == None: return locator

        return par + ":" + locator

    def get_accounts(self, acct=None, pfx=""):

        if acct == None: acct = ""

        s = set()

        for tx in self.transactions:
            for k in tx["splits"].keys():
                if k.startswith(acct):
                    s.add(k)

        return list(s)

    def is_debit(self, acct):
        if acct.startswith("Income"): return True
        if acct.startswith("Equity"): return True
        if acct.startswith("Expense"): return True
        return False

    # Get vendor by vendor ID, returns Vendor object
    def get_vendor(self, id):
        raise RuntimeError("Not implemented")

    # Get list of all vendors, list of Vendor objects
    def get_vendors(self):
        raise RuntimeError("Not implemented")

    # Create a vendor
    def create_vendor(self, id, currency, name):
        raise RuntimeError("Not implemented")

    # Get a currency given the mnemonic.  Returns a Commodity object.
    def get_currency(self, mn):
        raise RuntimeError("Not implemented")

    # Get next bill ID given vendor
    def next_bill_id(self, vendor):
        raise RuntimeError("Not implemented")

    # Createa a bill
    def create_bill(self, id, currency, vendor, date_opened):
        raise RuntimeError("Not implemented")

    # Add a bill entry to a bill
    def create_bill_entry(self, bill, date_opened):
        raise RuntimeError("Not implemented")

    # Get our 'special' predefined vendor for VAT returns.
    def get_vat_vendor(self):
        raise RuntimeError("Not implemented")

    # Post the VAT bill to a liability account.
    def post_vat_bill(self, billing_id, bill_date, due_date, vat, notes, memo):
        raise RuntimeError("Not implemented")

