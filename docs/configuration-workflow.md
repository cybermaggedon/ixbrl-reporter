
## Configuration workflow

`gnucash-ixbrl` is not simple to configure.  If the configuration files
supplied work for your business (and you should assume that they won't),
you could get accounts with little work.

However, it is very likely that you'll need to tailor the reports to work
with your business.  This configuration is not trivial.

If you need any of the taxonomy features that aren't covered in the taxonomy
configuration, then you'll need to edit taxonomy configuration also, which is
also complex.  You will need familiarity with the iXBRL taxonomies with which
you are working.

The configuration files hold:
- Template business metadata e.g. business name, address, etc.
- Accounting information flows, such as which GnuCash accounts are
  to be used, how the information is combined.
- A description about the structure, such as which accounting tables are
  presented.
- The iXBRL taxonomies, and how the accounting information is tagged.
- Structured notes, which are plain language explanations of things in the
  accounts.  The notes can be configured using markup and computations so
  that they are automatically created from accounting data.

A logical workflow in generating a report is:
- To study the GnuCash setup and work out which accounts contain relevant
  information.
- Configure the computation workflows, so that a plain-text output presents
  accounting tables with the right information for each accounting table.
  Plaintext output works without taxonomies, so it is a useful stepping
  stone in creating reports.
- Once you have the computations working, you can put the report layout
  together so that the HTML output looks right.
- Finally, you can work through the taxonomy configuration so that the
  information in the report is tagged correctly.  This is the most
  complex step and requires a good understanding of the data model.

### Empty configuration file

This is a basic structure which does nothing useful:
```
accounts:
  # Filename of GnuCash accounts
  file: example.gnucash
metadata: {}
computations: []
workflows: []
elements:
- id: report
  kind: composite
  elements: []
```

When you run `gnucash-ixbrl`, you get no output:
```
scripts/gnucash-ixbrl docs/simple1.yaml report text
```

This basic structure, describes the filename of the GnuCash accounts file,
has an empty metadata section, no computations, no workflows.  There is a
single element called `report` which references no other elements.  This
is the smallest configuration file which produces no errors.

### An empty worksheet

This is still in the 'does nothing useful' category.  Modifications are:
- A worksheet called `profit`.  This worksheet is useless because it has no
  calculations to display.
- An element called `profit` which references the `profit` worksheet.
- The `profit` element has been added to the `report` element.
- `metadata.report.periods` has been defined, because worksheets need
  the report periods to be defined.

```
accounts:
  # Filename of GnuCash accounts
  file: example.gnucash
metadata:
  report:
    periods:
    - name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
    - name: '2020'
      start: '2019-09-01'
      end: '2020-08-31'
computations: []
worksheets:
- id: profit
  kind: multi-period
  computations: []
elements:
- id: report
  kind: composite
  elements:
  - profit
- id: profit
  kind: worksheet
  title: Profit
  worksheet: profit
```

The output is slightly different:
```
scripts/gnucash-ixbrl docs/simple1.yaml report text
```
produces:
```
*** Profit ***
                                               2021       2020  
```

This is an empty worksheet.  There are two columns for the time periods,
but no values are displayed as there are no computations.

### Some computations

Let's calculate profit.  Naive calculation: profit is income
minus expenses.  In the GnuCash accounts there is a hierarchy of income
accounts under the top-level Income account, and a hierarchy of expense
accounts under the top-level Expense account.

The two changes are:
- Add `income` and `expenses` computations, referencing the GnuCash
  `Income` and `Expense` accounts.
- Add `income` and `expense` to the worksheet.

```
accounts:
  # Filename of GnuCash accounts
  file: example.gnucash
metadata:
  report:
    periods:
    - name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
    - name: '2020'
      start: '2019-09-01'
      end: '2020-08-31'
computations:
- id: income
  kind: line
  description: Income
  period: in-year
  accounts:
  - Income
- id: expenses
  kind: line
  description: Expenses
  period: in-year
  accounts:
  - Expenses
worksheets:
- id: profit
  kind: multi-period
  computations:
  - income
  - expenses
elements:
- id: report
  kind: composite
  elements:
  - profit
- id: profit
  kind: worksheet
  title: Profit
  worksheet: profit
```

Now the output is useful.  The reference to `Income` in GnuCash pulls in all
transactions in that account and subaccounts:
```
*** Profit ***
                                               2021       2020  

Income                                  :  18824.00    4212.00  

Expenses                                : (17378.51)  (2738.12) 
```

### Summing values

The next change is:
- Add the `profit` computation to the `computations` section.
- Add the `profit` computation to the worksheet.

```
accounts:
  # Filename of GnuCash accounts
  file: example.gnucash
metadata:
  report:
    periods:
    - name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
    - name: '2020'
      start: '2019-09-01'
      end: '2020-08-31'
computations:
- id: income
  kind: line
  description: Income
  period: in-year
  accounts:
  - Income
- id: expenses
  kind: line
  description: Expenses
  period: in-year
  accounts:
  - Expenses
- id: profit
  kind: sum
  description: Profit
  period: in-year
  inputs:
  - income
  - expenses
worksheets:
- id: profit
  kind: multi-period
  computations:
  - income
  - expenses
  - profit
elements:
- id: report
  kind: composite
  elements:
  - profit
- id: profit
  kind: worksheet
  title: Profit
  worksheet: profit
```

The output contains profit which is a sum of the (positive) income and
(negative) expenses.

```
*** Profit ***
                                               2021       2020  

Income                                  :  18824.00    4212.00  

Expenses                                : (17378.51)  (2738.12) 

Profit                                  :   1445.49    1473.88  
```

### Groups

There is an alternative way of presenting this information, which is
to present profit as a total, and income/expenses as line items.

Changes:
- Change the `profit` computation from a `sum` to a `group`.
- Remove the `income` and `expenses` lines from the worksheet.

```
accounts:
  # Filename of GnuCash accounts
  file: example.gnucash
metadata:
  report:
    periods:
    - name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
    - name: '2020'
      start: '2019-09-01'
      end: '2020-08-31'
computations:
- id: income
  kind: line
  description: Income
  period: in-year
  accounts:
  - Income
- id: expenses
  kind: line
  description: Expenses
  period: in-year
  accounts:
  - Expenses
- id: profit
  kind: group
  description: Profit
  period: in-year
  inputs:
  - income
  - expenses
worksheets:
- id: profit
  kind: multi-period
  computations:
  - profit
elements:
- id: report
  kind: composite
  elements:
  - profit
- id: profit
  kind: worksheet
  title: Profit
  worksheet: profit
```

Output is:
```
*** Profit ***
                                               2021       2020  

Profit:
  Income                                :  18824.00    4212.00  
  Expenses                              : (17378.51)  (2738.12) 
Total                                   :   1445.49    1473.88  
```

### Getting started with iXBRL

As before, let's do the minimal structure for useless output.

Changes:
- Added `taxonomy` section and reference to a file.
- Added `metadata.report.currency` which is needed.

```
accounts:
  # Filename of GnuCash accounts
  file: example.gnucash
taxonomy:
  file: tax.yaml
  id: my-taxonomy
metadata:
  business:
    company-number: '12345678'
    company-name: 'Example Biz Ltd.'
  report:
    currency: GBP
    periods:
    - name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
    - name: '2020'
      start: '2019-09-01'
      end: '2020-08-31'
computations:
- id: income
  kind: line
  description: Income
  period: in-year
  accounts:
  - Income
- id: expenses
  kind: line
  description: Expenses
  period: in-year
  accounts:
  - Expenses
- id: profit
  kind: group
  description: Profit
  period: in-year
  inputs:
  - income
  - expenses
worksheets:
- id: profit
  kind: multi-period
  computations:
  - profit
elements:
- id: report
  kind: composite
  elements:
  - profit
- id: profit
  kind: worksheet
  title: Profit
  worksheet: profit
```

The basic useless taxonomy goes in a file called `tax.yaml` because that
is the filename we used in the other configuration file:

```
taxonomy:
  my-taxonomy:
    namespaces: []
    schema: []
    contexts: []
    metadata: []
    document-metadata: []
```

The output *is* useful.  :)

```
scripts/gnucash-ixbrl docs/simple1.yaml report ixbrl > out.html
```

If you view that page in a web browser, you should see the Profit worksheet
presented properly.  However, there is no iXBRL tagging.  The values
presented are not known in the taxonomy so are not tagged.

### iXBRL tagging of report data

We're going to use the FRS-102 taxonomy here.  You can view that here:
[FRS-101](https://uk-taxonomies-tdp.corefiling.com/yeti/resources/yeti-gwt/Yeti.jsp).

Changes:
- Added `schema` reference for the FRS-102 taxonomy. This should appear in the
  taxonomy documentation.
- Added `namespaces` section which declares a set of XML namespaces required
  by this schema.  Again, should be in the documentation - the data is
  in the taxonomy schema.
- Tags mapping our computations (income, expenses, profit) to iXBRL tags.
  The closest things in FRS-102 are `GrossProfit`, `AdminstrativeExpenses`
  and `ProfitLoss`, which will do for this simple example.

```
taxonomy:
  my-taxonomy:
    namespaces:
      uk-bus: http://xbrl.frc.org.uk/cd/2021-01-01/business
      uk-core: http://xbrl.frc.org.uk/fr/2021-01-01/core
      uk-direp: http://xbrl.frc.org.uk/reports/2021-01-01/direp
      uk-geo: http://xbrl.frc.org.uk/cd/2021-01-01/countries
    schema:
    - https://xbrl.frc.org.uk/FRS-102/2021-01-01/FRS-102-2021-01-01.xsd
    contexts: []
    metadata: []
    document-metadata: []
    tags:
      income: uk-core:GrossProfit
      expenses: uk-core:AdministrativeExpenses
      profit: uk-core:ProfitLoss
```

The HTML output won't look any different in a browser, but if you peek
in the file with a text editor, you should see some iXBRL tags. e.g.
```
  <div class="period value">
    <ix:nonFraction name="uk-core:GrossProfit" contextRef="ctxt-1"
        format="ixt2:numdotdecimal" unitRef="GBP"
	decimals="2">4,212.00</ix:nonFraction>
  </div>
```

### Document metadata

The report has all the account fields tagged, but doesn't mention the
company name anywhere, so we can add that to the hidden tags section.

Changes go in `tax.yaml`:
- Added `company-name` field to `document-metadata`.
- Define the `company-name` field in the `metadata` section by referencing
  configuration value `metadata.business.company-name`.
- Define an XBRL context called `business` which references the company
  number.
- Define an XBRL context called `report-period` which is derived from
  `business`, but adds a time period to the `business` context.

The result is a hidden iXBRL tag:
```
    <ix:hidden>
        <ix:nonNumeric name="uk-bus:EntityCurrentLegalOrRegisteredName"
	contextRef="ctxt-0">Example Biz Ltd.</ix:nonNumeric>
    </ix:hidden>
```


