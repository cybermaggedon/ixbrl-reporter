
# `gnucash-ixbrl`

## Introduction

This is a utility which allows gnucash accounts to be presented as iXBRL
report output.  iXBRL is XHTML with embedded XBRL tags so that the document
can be viewed in an HTML browser, but embedded tags all the underlying data to
be extracted by automated tools.  This allows the same accounts to be usable
by a human, and also by automated data extraction tools.

Included in this repo are example accounts and configuration files exist
which output:
- Company accounts for UK Companies House filing using the FRS-101 taxonomy.
- UK HMRC corporation tax filing using the CT600 schema.
- UK HMRC detailed-profit-and-loss filing using the DPL schema.

With the right configuration files, other taxonomies would work, the
configuration files are complex.

Plain-text report output is also supported as a byproduct.

This code comes with no warranty whatsoever.  See the [LICENSE] file for
details.

This can be used to automate production of account information so that you
can get an up-to-date balance sheet out of gnucash.  

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
gnucash-ixbrl ch.yaml report ixbrl > out.html
```

Corporation tax filing:

```
gnucash-ixbrl ct.yaml report ixbrl > ct600.html
```

Detailed profit-and-loss:

```
gnucash-ixbrl dpl.yaml report ixbrl > dpl.html
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

