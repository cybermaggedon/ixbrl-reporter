
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

This sections describes a set of report computations.  These can be
types: `group` which fetches information from gnucash accounts.
Also, `computation` which sums information from other `group` and `computation`
elements.

### `group` type

Here's an example.  The group is called `fixed-assets`, with an appropriate
description.  A group consists of zero or more lines, each line has a list
of Gnucash accounts to access.  When the group is displayed each line is
shown with its total for that set of accounts, and then there's a total for
all the lines.
```
computations:
- id: fixed-assets
  description: Fixed Assets
  kind: group
  period: at-end
  lines:
  - accounts:
    - Assets:Capital Equipment
    description: Tangible Assets
    id: tangible-assets
    kind: line
    period: at-end
```

The output might look like this:

```
Fixed Assets:
  Tangible Assets                       :    512.00
Total                                   :    512.00
```

In gnucash, things that cause money to go away (e.g. liabilities) are negative.
In iXBRL they are normally positive, so you can set the `sign` field to
`reversed` to turn something which is normally a Gnucash negative into an
iXBRL positive.  This is done in the taxonomy configuration file.

When examining Gnucash accounts the `group` normally looks at transactions
from time immemorial (1970) up until the end of the account period.
This is correct for balance sheets where you are analysing accumulation and
want to analyse at a point in time.  But not correct for income/expenses where
you are analysing flow, and only want to account in-year.
This is controlled with the `period` attribute.  Set to `at-end` to examine
transactions from the beginning from time immemorial to the end of the period,
`at-start` to examine transactions prior to the accounting period, and
`in-year` to examine transactions only within the accounting period.  The
`period` output affects the time information provided in iXBRL contexts
related to that data element.  `at-start` and `at-end` results in association
of contexts with an instant of time.  `in-year` results in association of
contexts with a period of time.  `at-end` is the default.

If the `line` list is empty i.e. there are no line items, the group
will collapse down to a nil line.

Regarding iXBRL output, the taxonomy configuration file is used to map
computations (by the `id` attribute) to iXBRL tag names.

The `hide-breakdown` attribute causes a group to be shown as a total
without individual lines shown.

### `computation` type

The computation type sums information from other groups or computations.
e.g. we can compute net current assets by summing current assets etc.:

```
- id: net-current-assets
  kind: computation
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

## `worksheets`

Computations describe internal data flows, but don't cause any output.
The next layer up from computations is worksheet, which describe a set
of computations which should be tabulated together.

Here's a balance sheet exmaple:

```
worksheets:
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

## `elements`

Worksheets don't produce any output, either.  It is the `elements`
configuration describes what goes into a report.

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

