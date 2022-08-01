
# `ixbrl-reporter`

## Summary

This is a command-line utility which creates iXBRL-tagged financial reports
from configuration templates and account data.  It currently supports account
information from GnuCash files, and also a CSV file of transactions.

## Discuss

There's a #ixbrl-reporter channel on our Discord server if you want
to discuss... https://discord.gg/3cAvPASS6p

## Note

The configuration files used by ixbrl-reporter are complex.  See
[`ixbrl-reporter-jsonnet`](https://github.com/cybermaggedon/ixbrl-reporter-jsonnet) for an easier way to manage the configuration files.

## Summary

This code is intended for use with `ixbrl-reporter`.

Using `ixbrl-reporter` requires a complex configuration file, or set of
configuration files.  An internal import/reference mechanism was introduced
to allow the configuration files to be modulariesd, but the mechanism is
still not ideal.

This repo implements JSONNET templates for construction of configuration
files for `ixbrl-reporter` which makes the matter more manageable.

Jsonnet (see jsonnet.org) is a programming language (invented by Google)
which extends JSON with programming constructs.  Jsonnet is specifically
designed to make it easy to build configuration files; it supports object
templating and extension.

## iXBRL

The iXBRL format is commonly used to describe regulatory account information
which companies must publish.  Different schemas are in use in different
places in the world.  The example account and report data included in this
project uses schemas which are used in the UK reporting regime, and there
is also a minimalistic ESEF example, but it is possible to define other
taxonomies.

iXBRL stands for "Inline XBRL".  It was built on the XBRL standard
(eXtensible Business Reporting Language).  iXBRL is HTML with embedded XBRL
tags so that the document can be viewed in an HTML browser and read by
a human, but the tags are also machine-readable.  This allows the same
accounts to be usable by a human, and also by automated data extraction tools.

## Examples

Included in this repo are example accounts and configuration files exist
which output:
- Company accounts for UK Companies House filing using the FRS-102 taxonomy.
- UK HMRC corporation tax filing using the CT600 schema and Detailed Profit
  and Loss schema in a single document.
- ESEF filing configuration for an English-language filing as well as
  French.

Configuration files can be written for other taxonomies.

## Other outputs

Plain-text report output is supported (semi-useful), as is plain-text
HTML output created by stripping the iXBRL tags.

## Motivation

iXBRL report generation is presently convoluted.  Generally people generate
financial reports, or use an accountant to create the reports, and then
send the report files away for a human to semi-automatically tag using an
iXBRL tagging tool, which takes some number of days and costs at least €150.

This tool demonstrates auto-generating reports with the right tags in the
first place.

The overheads in configuring reports and iXBRL output with `ixbrl-reporter`
is not small, but that's an up-front cost, once set-up, up-to-date reports
can be generated.

## Warranty

This code comes with no warranty whatsoever.  See the [LICENSE](LICENCE) file
for details.  Further, I am not an accountant.  Even if I were, I would not be
YOUR accountant.  It is possible that this code could be useful to you in
meeting regulatory reporting requirements for your business.  It is also
possible that the software could report misleading information which could
land you in a lot of trouble if used for regulatory purposes.  Really, you
should check with a qualified accountant.

## Configuration overview

`ixbrl-reporter` configuration is complex: If the configuration files
supplied work for your business you could get accounts with little work.

However, it is very likely that you'll need to tailor the reports to work
with your business.  The information flows are described
in [Information flows](docs/information-flows.md).

## Installing

There is a dependency on one of the `gnucash`, `piecash` or `csv` Python
modules:

- The `gnucash` Python support is built from the GnuCash source code tree
  itself.  It is currently only distributed with Linux packages.  You cannot
  use this on Windows or MacOS.  See
  <https://wiki.gnucash.org/wiki/Python_Bindings> for installation, but on
  Linux it is generally installed when you install the gnucash package.
  It is not possible to install the `gnucash` module using PyPI.
- The `piecash` Python support can be download using `pip` or your favourite
  Python package manager.  It works on Linux, MacOS and Windows.  However,
  it only supports the Sqlite or Postgres GnuCash formats, and not the
  XML format which is the default.
- The `csv` Python module is bundled with Python.

It is possible to convert a GnuCash file to Sqlite format by using
GnuCash, select Save As... and selecting Sqlite.

```
pip3 install git+https://github.com/cybermaggedon/ixbrl-reporter
```

## Usage

```
ixbrl-reporter <config> <report> <format>
```

Where:
- `config` specifies a configuration file.  See
  [Configuration File](docs/config.md).
- `report` specifies a report tag.
- `format` specifies output format.  `text` outputs plain text, `ixbrl`
  outputs iXBRL (XHTML tagged with XBRL tags) and `html` outputs HTML, which
  is iXBRL with the XBRL tags removed.

The examples use files in the git repo.  Clone the git repo to run this
stuff:

```
git clone https://github.com/cybermaggedon/ixbrl-reporter
```

Example, Companies House accounts. You should be able to view the resultant
HTML in a browser:

```
ixbrl-reporter config.yaml report ixbrl > accts.html
```

Corporation tax filing:

```
ixbrl-reporter config-corptax.yaml report ixbrl > ct.html
```

ESMA ESEF filing:

```
ixbrl-reporter config-esef.yaml report ixbrl > esef.html
```

Check out the awesome Graffiti tool for viewing iXBRL tags in a document.
The basic version is free.  It's just a bookmark in your browser!  Once
your iXBRL document is loaded in the browser, invoke the bookmark and
iXBRL tag navigation is seamlessly added to the document you are looking at.
https://stechanalytics.com/#Graffiti

## Configuration

All the configuration is in YAML, and there are various configuration
files which are linked together.  If the templates work for you, you should
only have to change `config.yaml` and `metadata.yaml`.

- `config.yaml` is the top-level configuration file which imports the
  other configuration files.  Of interest, is the `accounts` section which
  specifies which GnuCash file to use.  There is also a `report` setting
  which describes which report definition to import.  Also a `pretty-print`
  setting which causes HTML to be output with indented spacing to make it
  easier to read if you have to debug something.
- `metadata.yaml` contains information specific to the business the report
  is about, such as name of business, address, company identifiers and so
  on.  You would edit this to describe your business.
- Taxonomy definitions under the `taxonomy` directory specify the mapping
  between identifiers and the iXBRL tagging.  If the report templates do
  what you need, you won't need to change this.
- Report configuration files under the `report` directory.  Think of these
  as report templates. They define the structure of information going into
  the report.  There is a `ch` sub-directory containing various kinds of
  Companies House filing templates.  Also an `hmrc` sub-directory containing
  the HMRC corporation tax filing template.  If these report configurations do
  what you want, you don't need to change them.
- `directors-report.yaml`, `accountants-report.yaml`, `auditors-report.yaml`,
  `notes.yaml` are used to provide specific sections of the company accounts.
  These are only needed for more complex reports, for a micro-entity account
  filing, these are not used.

All configuration files are YAML.

See [Configuration File](docs/config.md).

## Screenshots of output

[Screenshots](docs/screenshots.md)

## Other things to try

Having created iXBRL, you can try loading into
[Arelle](https://arelle.org/arelle/) which is an iXBRL development tool.
In Arelle, you can invoke a validation and check the output matches the
schema.

Once Arelle is installed, you can install the Workiva
[ixbrl-viewer](https://github.com/Workiva/ixbrl-viewer).  When an iXBRL
document is loaded into Arelle, the document is automatically loaded into
a browser with markup so that you can navigate the tags and discover tagged
information.  With the iXBRL viewer when you hover over tagged information,
it is highlighted, clicking opens up the metadata viewer.

### Test suite / examples

See the `test` directory.

```
sh test/run_all
```

Output in `output`.

## License

Copyright (c) Accounts Machine Limited, 2020-2022
Licenced under the GPL version 3 licence, see the [LICENSE](LICENCE) file

