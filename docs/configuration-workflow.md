
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

This is an empty worksheet.  There are two columns for the time period,
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

Now the output is useful:
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

### iXBRL

FIXME: explain tagging etc.