
# Taxonomy configuration

The configuration file is in YAML format, and consists of the following parts:

## `taxonomy.TAXONOMY`

where TAXONOMY is the name of the taxonomy.

## `taxonomy.TAXONOMY.contexts`

The `contexts` section predefines contexts which are used in
`metadata` definitions.  The definition consists of:

- `from` field specifies the context which is a parent of this context.
   This context imports all definitions from the specified context.
   If not specified, an empty context is the starting point.
- `entity` specifies the context's entity identifier.  This can be a
  literal string, or configuration key.  `scheme` should be specified
  to describe the entity identifier scheme.
- `segments` specifies a set of context segment members.  The `lookup` part
  of the taxonomy configuration file maps segment ID/value pairs to real iXBRL
  names.
- `period` specifies the configuration key of a period.  Periods are
  a YAML object with a `name` (string), `start` and `end` (dates).
  The name is irrelevant, just the `start` and `end` date are used.
- `instant` specifies the configuration key of a date.

e.g.

```
taxonomy:
  frs101:
    contexts:
    - entity: metadata.business.company-number
      id: business
      scheme: http://www.companieshouse.gov.uk/
    - from: business
      id: report-period
      period: metadata.report.periods.0
    - from: business
      id: report-date
      instant: metadata.report.date
    - from: report-period
      id: industry-sector
      segments:
        industry-sector: metadata.business.industry-sector
```

## `taxonomy.TAXONOMY.metadata`

Specifies a set of metadata fields which can be invoked from various
places (e.g. notes).

```
    metadata:
    # Metadata from a configuration file
    - config: metadata.report.title
      context: report-period
      id: report-title
    - config: metadata.report.date
      context: report-date
      id: report-date
      kind: date
    - config: metadata.report.authorised-date
      context: report-date
      id: authorised-date
    - id: period-start
      kind: date
      context: report-date
      config: metadata.report.periods.0.start
    - id: test
      kind: value
      value: Hello world
```

When a `config` field is specified, it is used to get a value, otherwise
the `value` field specifies a static value.  The `kind` field describes the
type (one of `string`, `money`, `bool`, `number`, `count`, `date`).

## `taxonomy.TAXONOMY.document-metadata`

Specifies a list of metadata fields (defined in ...`metadata`) which are
included in the `hidden` section in an iXBRL file.  These are metadata
which are present, but not visible in the browser.

e.g.
```
    document-metadata:
    - report-title
    - report-date
    - authorised-date
    - period-start
    - period-end
    - company-name
```

Just the metadata identifiers are specified.

## `taxonomy.TAXONOMY.lookup`

This section maps segment information to real iXBRL tags.

```
    lookup:

      # This is the segment name
      accounting-standards:

        # The segment name gets mapped to this iXBRL dimension
        dimension: uk-bus:AccountingStandardsDimension

        # And then, the segment value gets mapped to dimension values thus...
        map:
          frs101: uk-bus:FRS101
          frs102: uk-bus:FRS102
          frsse: uk-bus:FRSSE
          full-irs: uk-bus:FullIFRS
          micro-entities: uk-bus:Micro-entities
          other-standards: uk-bus:OtherStandards
          small-entities-regime: uk-bus:SmallEntities
```

## `taxonomy.TAXONOMY.namespaces`

This section specifies namespaces which are added to the iXBRL document
when this taxonomy is used.  A set of standard iXBRL namespaces are added by
default.  You only need to add non-standard ones specific to this taxonomy.
e.g.

```
    namespaces:
      uk-bus: http://xbrl.frc.org.uk/cd/2021-01-01/business
      uk-core: http://xbrl.frc.org.uk/fr/2021-01-01/core
      uk-direp: http://xbrl.frc.org.uk/reports/2021-01-01/direp
      uk-geo: http://xbrl.frc.org.uk/cd/2021-01-01/countries
```

## `taxonomy.TAXONOMY.schema`

Specifies the taxonomy definition URL e.g.
```
    schema: https://xbrl.frc.org.uk/FRS-102/2021-01-01/FRS-102-2021-01-01.xsd
```

## `taxonomy.TAXONOMY.notes`

Specifies the pre-defined note tokens.

```
    notes:
      company: 'The company is a private company limited by shares and is
        registered in England and Wales number ~[company-number].
        The registered address is: ~[contact-address1::, ]
        ~[contact-address2::, ] ~[contact-address3::, ]
        ~[contact-location:: ] ~[contact-postcode].'
```

## `taxonomy.TAXONOMY.sign-reversed`

In gnucash, things that cause money to go away (e.g. liabilities) are negative.
In iXBRL they are normally positive, so you can set the `sign` field to
`reversed` to turn something which is normally a Gnucash negative into an
iXBRL positive.  This is done in the taxonomy configuration file.

Specifies a set of fact identifiers whose values have a reverse meaning
to what they do in GnuCash.  e.g. expenses come out as negative in GnuCash
to describe cash leaving the business.
However, in the iXBRL schema definition expenses are typically positive
numbers.

```
    sign-reversed:
      accruals-and-deferred-income: true
```

## `taxonomy.TAXONOMY.tags`

Maps fact identifiers to their iXBRL tag names in this taxonomy.
```
    tags:
      accounting-standards: uk-bus:AccountingStandardsApplied
      company-name: uk-bus:EntityCurrentLegalOrRegisteredName
      company-number: uk-bus:UKCompaniesHouseRegisteredNumber
```

