
# `gnucash-ixbrl`

## Introduction

This is a utility which allows accounts managed by the excellent
[GnuCash](gnucash.org) accounting software to be presented as iXBRL
report output.  iXBRL is commonly used to describe regulatory account
information which companies must publish annually.  Different schemas are
in use in different places in the world.  The example account and report
data included in this project uses schemas which are used in the UK
reporting regime.

iXBRL stands for "Inline XBRL".  It was inspired by the XBRL standard
(Extensible Business Reporting Language).  iXBRL is HTML with embedded XBRL
tags so that the document can be viewed in an HTML browser and read by
a human, but the tags are also machine-readable.  This allows the same
accounts to be usable by a human, and also by automated data extraction tools.

Included in this repo are example accounts and configuration files exist
which output:
- Company accounts for UK Companies House filing using the FRS-101 taxonomy.
- UK HMRC corporation tax filing using the CT600 schema and Detailed Profit
  and Loss schema in a single document.
- UK HMRC detailed-profit-and-loss filing using the DPL schema.

With the right configuration files, other taxonomies would work, the
configuration files are complex to write.  This code is all command line,
and largely only work in Linux.

Incidentally, plain-text report output is also supported as a byproduct of
creating the reports.  This is useful in the workflow of constructing
report configuration.

## Motivation

The overheads in configuring report and iXBRL output with `gnucash-ixbrl`
is not small, but that's an up-front cost.

The motivation is that once set up, it is trivial to generate reports,
with the latest, accurate information without constantly copying boiler-plate
text into reports.  It isn't difficult to generate reports dynamically.
Automating business report for low on-going costs, and real-time delivery of
information.

## Warranty

This code comes with no warranty whatsoever.  See the [LICENSE](LICENCE) file
for details.  Further, I am not an accountant.  It is possible that this code
could be useful to you in meeting regulatory reporting requirements for your
business.  It is also possible that the software could report misleading
information which could land you in a lot of trouble if used for regulatory
purposes.  Really, you should check with a qualified accountant.

## Configuration overview

`gnucash-ixbrl` is not simple to configure.  If the configuration files
supplied work for your business (and you should assume that they won't),
you could get accounts with little work.

However, it is very likely that you'll need to tailor the reports to work
with your business.  This configuration is not trivial.  It is described
in [Configuration Workflow](docs/configuration-workflow.md).

## Installing

There is a dependency on the `gnucash` Python module, which cannot be installed
from PyPI.  See <https://wiki.gnucash.org/wiki/Python_Bindings> for
installation.  On Linux (Debian, Ubuntu, Fedora), the Python modules are
available on package repositories.  MacOS and Windows builds of GnuCash are
reportedly not shipping with Python APIs at the moment.

```
pip3 install git+https://github.com/cybermaggedon/gnucash-ixbrl
```

## Usage

```
gnucash-ixbrl <config> <report> <format>
```

Where:
- `config` specifies a configuration file.  See
  [Configuration File](docs/config.md).
- `report` specifies a report tag.
- `format` specifies output format.  `text` outputs plain text, `ixbrl`
  outputs iXBRL (XHTML tagged with XBRL tags) and `html` outputs HTML, which
  is iXBRL with the XBRL tags removed.

The examples use files in the git repo.  Clone the git repo to run this
stuff.

Example, Companies House accounts. You should be able to view the resultant
HTML in a browser.


```
gnucash-ixbrl company-accounts.yaml report ixbrl > out.html
```

Corporation tax filing:

```
gnucash-ixbrl corporation-tax.yaml report ixbrl > ct600.html
```

Detailed profit-and-loss:

```
gnucash-ixbrl profit-and-loss.yaml report ixbrl > dpl.html
```

## Configuration

There are two configuration files: the configuration file you specify
on the command line specifies the report structure.  It references a
taxonomy configuration file which specifies the schema and field mappings.

Both configuration files are YAML.

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

