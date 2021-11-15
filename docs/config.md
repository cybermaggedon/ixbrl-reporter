
# Configuration

The configuration file is YAML file.  There is also a
[Taxonomy configuration file](taxonomy.md).

The configuration file consists of the following parts:

## `accounts`

This is where you specify the gnucash accounts filename:

```
accounts:
  file: example.gnucash
```
## `taxonomy`

References the taxonomy configuration file.  Schema filename and
taxonomy ID.
```
taxonomy:
  file: taxonomy/frs101.yaml
  id: frs101
```

## `metadata`

### `metadata.business`

This is where you describe your business e.g.
```
  business:
    activities: Computer security consultancy and development services
    average-employees:
    - 2
    - 1
    company-name: Example Biz Ltd.
    company-number: 012345678
    company-formation:
      country: england-and-wales
      date: '2017-04-05'
      form: private-limited-company
    vat-registration: GB012345678
    contact:
      name: Corporate Enquiries
      address:
      - 123 Leadbarton Street
      - Dumpston Trading Estate
      county: Minchingshire
      location: Threapminchington
      country: UK
      email: corporate@example.org
      phone:
        area: '7900'
        country: '+44'
        number: '0123456'
        type: landline
      postcode: QQ99 9ZZ
    directors:
    - A Bloggs
    - B Smith
    - C Jones
    industry-sector: m
    is-dormant: false
    sic-codes:
    - '62020'
    - '62021'
    website:
      description: Corporate website
      url: https://example.org/corporate
```

### `metadata.report`

Some report configuration.  Notice that report periods are defined.

```
  report:
    accounting-standards: micro-entities
    accounts-status: audit-exempt-no-accountants-report
    accounts-type: abridged-accounts
    authorised-date: '2021-08-31'
    balance-sheet-date: '2021-08-31'
    currency: GBP
    date: '2021-08-31'
    periods:
    - name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
    - name: '2020'
      start: '2019-09-01'
      end: '2020-08-31'
    signed-by: B Smith
    signing-officer: director2
    title: Unaudited Micro-Entity Accounts
```

The `signing-officer` element is a reference to which director signed off the
report in `metadata.business.directors`.  The value `director1` means the
first director did so, `director2`, the 2nd etc.

### `metadata.tax`

This configuration is referenced in other bits of the `ct.yaml` configuration
file, and provides some configuration for tax reports:

```
  tax:
    utr: 0123456789
    period:
      name: '2021'
      start: '2020-09-01'
      end: '2021-08-31'
```

## `computations`

This sections describes the flow information which makes up the computations.
The types are:
- `line` which fetches information from GnuCash accounts.
- `group` describes the combination of a set of computations in a sum with
  a total.
- The `sum` type is similar to `group`, but presents only a total.
- The `constant` describes data which is taken from the configuration file,
  not a GnuCash account.
- The `apportion` type takes a computation and works out a proportion
  based on a number of days in a period.

The type of computation is described in the `kind` element in its
configuration.

When examining Gnucash accounts, by default the computation looks at
transactions from time immemorial (1970) up until the end of the accounting
period.  This is correct for balance sheets where you are analysing
accumulation and want to analyse at a point in time.  But not correct for
income/expenses where you are analysing flow, and only want to look at
transactions in-year.  The `period` attribute is used to configure the
time period:  Set to `at-end` to examine
transactions from the beginning of time immemorial to the end of the period,
`at-start` to examine transactions prior to the accounting period, and
`in-year` to examine transactions only within the accounting period.

The `period` output affects the time information provided in iXBRL
contexts related to that data element.  `at-start` and `at-end`
results in association of contexts with an instant of time.  `in-year`
results in association of contexts with a period of time.  `at-end` is
the default.

### `line` type

An example:
```
lines:
- id: tangible-assets
  kind: line
  description: Tangible Assets
  period: at-end
  accounts:
  - Assets:Machine Equipment
  - Assets:Plant Equipment
```

This computation adds up relevant transactions in the period in all
accounts listed in the `accounts` element and forms a total.  In an
accounting table, it might appear as:

```
Tangible Assets                         :    512.00
```

As with all computations, there is an `id` element which is used to
identify the computation in configuration files.  There is also a
`period` element which describes the timeframe which is examined.

If a `line` computation has an empty account list, the value is zero.

### `group` type

The `group` computation takes a set of other computations (of any type)
and combines them in a sum.  When included in an accounting table, they
are presented as an itemised list of values with a total.  Here's an example.
The group is called `current-assets`, with an appropriate
description.  An `inputs` element references a set of computations by ID.
Note that computation references can only reference computations earlier
in the configuration file.

```
- description: Current Assets
  id: current-assets
  kind: group
  period: at-end
  inputs:
  - debtors
  - vat-refund-owed
  - bank
```
The output might look like this:

```
Current Assets:
  Debtors                               :    234.12
  VAT Refund Owed                       :    102.81
  Bank                                  :   4001.20
Total                                   :   4338.13
```

If the `inputs` list is empty i.e. there are no line items, the group
will collapse down to a single line zero total.

The `hide-breakdown` attribute causes a group to be shown as a total
without individual lines shown, which makes it the same as a `sum` type.

### `sum` type

The computation type sums information from other computations.
e.g. we can compute net current assets by summing current assets etc.:

```
- id: net-current-assets
  kind: sum
  description: Net Current Assets
  inputs:
  - current-assets
  - prepayments-and-accrued-income
  - creditors-within-1-year
```

The output is a single line e.g.

```
Net Current Assets                      :   8080.00
```

### Sign

Normally, transactions have the "correct" sign applied to them.  Income,
Equity and Assets are positive.  Expenses and Liabilities are negative.
That way, when information is combined (e.g. Income and Expenses) the sum is
useful (e.g. Profit).  You can reverse the sign on any computation:

```
reverse-sign: true
```

This is rarely needed.  One example of usage would be to 'correct' a value
which has been included in a computation.  For example, management expenses
typically includes depreciation.  If I want to see management expenses
without depreciation, adding `management-expenses` and `depreciaton`
will give the wrong result.  `management-expenses` is negative, and 
adding the `depreciation` expense will make the expense larger.
So, the computation can be made by taking a 'reversed' depreciation expense
and adding it to management expenses.

### iXBRL

Regarding iXBRL output, the taxonomy configuration file is used to map
computations (by the `id` attribute) to iXBRL tag names.  See
[Taxonomy Configuration](taxonomy.md).

### Segments

FIXME: Describe

## `worksheets`

Computations describe internal data flows, but don't cause any output.
Worksheets are a collection of computations. The worksheet specifies a
set of computations to output.  Worksheets just describe a set
of computations to show, not how any of the information is linked.  It is
possible to construct a worksheet that uses computations that aren't shown,
which may be confusing to the reader.  It's down to you to select a set of
computations that make sense together.

Here's a balance sheet exmaple:

```
- id: balance-sheet
  kind: multi-period
  computations:
  - fixed-assets
  - current-assets
  - prepayments-and-accrued-income
  - creditors-within-1-year
  - net-current-assets
  - total-assets-less-liabilities
  - creditors-after-1-year
  - provisions-for-liabilities
  - accruals-and-deferred-income
  - net-assets
  - capital-and-reserves
  - total-capital-and-reserves
```

The only currently supported worksheet type is `multi-period`.

## `elements`

Elements describe the structure of a report.  When `gnucash-ixbrl` is
invoked, the user selects an element to invoke.  Elements have
different types - the `composite` element is a container, and can combine a
set of elements into a single output.

```
elements:
- id: report
  kind: composite
  elements:
  - title
  - balance-sheet
  - profit-and-loss
  - fixed-assets
  - share-capital
  - notes
- id: title
  kind: title
  signature-image: signature.png
  signature-type: image/png
- id: balance-sheet
  kind: worksheet
  title: Balance Sheet
  worksheet: balance-sheet
- id: profit-and-loss
  kind: worksheet
  title: Income Statement
  worksheet: profit-and-loss
- id: fixed-assets
  kind: worksheet
  title: Fixed Assets
  worksheet: fixed-assets
- id: share-capital
  kind: worksheet
  title: Share Capital
  worksheet: share-capital
- id: notes
  kind: notes
  notes:
  - micro-entity-provisions
  - small-company-audit-exempt
  - no-audit-required
  - company
  - directors-acknowledge
  - software-version
  - 'note:~{supplementary-note:report-period=These are fictional accounts,
    references to real-world entities or persons is unintentional.}'
- id: heading
  kind: html
  root:
    tag: h2
    attributes:
      class: heading
      style: 'font-weight: bold'
    content:
    - tag: span
      content: 'Hello world'
- id: page1
  kind: page
  elements:
  - heading
  - notes
```

The entry point is the `report` element, at the top.  It is a `composite`
which means it builds a report from other elements.
The `title` element produces a report page.  The `worksheet` elements 
tabulate defined worksheets one per page.  Finally, the `notes` element
produces a list of notes.  

The `notes` section auto-generates report notes with appropriate company
data and iXBRL tags. e.g. `micro-entity-provisions` outputs a note which
says: "These financial statements have been prepared in accordance with the
micro-entity provisions."  `company` outputs something like "The company is
a private company limited by shares and is registered in England and Wales
number 012345678. The registered address is: 123 Leadbarton Street, Dumpston
Trading Estate, Threapminchington, Minchingshire QQ99 9ZZ."

Custom notes can be added with the `note:` prefix followed by any text you
want in the report.

### Note markup

Notes have a simple markup language.  iXBRL tags can be created
using a form such as `~{identifier=content}`.  A defined context can be
specified using `~{identifier:context=content}`.  A type can be
specified using `~{identifier:context:type=content}` where type is one
of `m`: money, `b`: boolean, `n`: number, `c`: count, `s`: string.  Only
string is supported currently.  Tags can be nested.

Canned metadata facts can be added using the form `~[tag-name]`.  The
`tag-name` metadata is specified in the taxonomy configuration file.
The longer form is `~[tag-name:prefix:suffix:null]`.  If the field
has a null value, the null text is output.  Otherwise, the tag-name is output,
iXBRL tagged, with the provided prefix and suffix added before and after.

Example:
```notes:
      company: 'The company is a private company limited by shares and is
        registered in England and Wales number ~[company-number].
        The registered address is: ~[contact-address1::, ]
        ~[contact-address2::, ] ~[contact-address3::, ]
        ~[contact-location:: ] ~[contact-postcode].'
```

This example adds comma-separation between elements of the address.
Although this particular schema provides for 3 lines of address, not all will
be present, and this mechanism adds commas to the output only where needed.

