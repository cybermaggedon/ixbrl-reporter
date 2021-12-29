
# Configuration

## Basic structure

The configuration uses YAML in a highly structured form.  We use a
dot-separated path specifier to reference configuration at various points.
For example, in the following configuration, the path specifier
`one.val1.first` would reference the number 42:

```
one:
- val1:
  - first: 42
  - second: 66
two:
- val1: hello world
```

The configuration can all be specified
in a single file, but to make things easier, the configuration can be
broken up.  There are two special 'markups' that have been introduced:
- A configuration value can be a string of the form `//import file`
  whereupon the data in the specified file is parsed as YAML and
  substituted at this point of the configuration.
- A configuration value can be referenced at other points in the configuration
  using `//ref path.to.value` whereupon the specified dot-separated path
  is used to lookup configuration data.

## `accounts`

This is where you specify the gnucash accounts filename, and the class
used to handle the accounts access. e.g.

```
accounts:
  kind: piecash
  file: example2.gnucash
```

In the example, you'll see this located at the top of `config.yaml`.

## `report.taxonomy`

This contains taxonomy data.  See [Taxonomy configuration file](taxonomy.md).

There is an example of taxonomy in the configuration file
`taxonomy/frs102.yaml`.

### `metadata`

This is where you describe specifics of your report and your business

There is an example specification in `metadata.yaml` which can be treated
as a template for your business.  There are various dates in here
which are important e.g. look for the `metadata.report.periods` which
defines the accounting periods the report is produced over.

The `metadata.business.signing-officer` element is a reference to which
director signed off the report in `metadata.business.directors`.
The value `director1` means the first director did so, `director2`, the 2nd
etc.

## `report.computations`

This sections describes the flow information which makes up the computations.
There are example computations in `report/ch/frs102-computations.yaml`.

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

## `report.worksheets`

Worksheets take a collection of computations and produce a financial table.
The main worksheet is the `simple` kind at the moment, we'll work on other
worksheets which give more control over the output in time.

See `report/ch/frs102-worksheets.yaml` for some examples.

Worksheets just describe a set of computations to show, not how any of the
information is linked.  It is possible to construct a worksheet that uses
computations that aren't shown, which may be confusing to the reader.  It's
down to you to select a set of computations that make sense together.

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

## `elements`

Elements describe the structure of a report.  When `ixbrl-reporter` is
invoked, the user selects an element to invoke.  Elements have
different types - the `composite` element is a container, and can combine a
set of elements into a single output.

```
elements:
- id: report
  kind: composite
  elements:
  - balance-sheet
  - notes
- id: balance-sheet
  kind: page
  elements:
  - kind: worksheet
    title: Balance Sheet
    worksheet: balance-sheet
- id: notes
  kind: page
  elements:
  - kind: html
    content:
      tag: div
      content:
      - tag: p
	content:
	- Here is note 1.
      - tag: p
	content:
	- Here is note 2.
```

The entry point is the `report` element, at the top.  When calling
`ixbrl-reporter` you have to specify this entry point.
`report` is a composite which includes two other elements, `balance-sheet`
and `notes`.  The `balance-sheet` demonstrates nested elements by
including a `worksheet` element within a `page` element.
The `notes` element embeds some HTML elements.

There are some example elements defined in the `report/ch/macros.yaml`
configuration file.

## Template expansion

Content of an `html` element can include text which is subject to expansion
if it begins with the `expand:` prefix.

A simple markup language is used.  iXBRL tags can be created
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
```
expand:The company number is ~[company-number].
```


