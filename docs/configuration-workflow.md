
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

