# Regression Tests

This directory contains regression tests that ensure iXBRL report generation remains consistent across changes.

## Quick Start

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all regression tests
pytest tests/regression/ -v

# Run a specific test configuration
pytest tests/regression/ -k "unaud-micro" -v
```

## What These Tests Do

1. Generate iXBRL reports from 15 different configurations
2. Extract key-value pairs from the generated reports
3. Compare against expected outputs stored in `/log/`
4. Flag any differences (excluding version fields)

## When Tests Fail

If tests fail due to intentional changes:

1. Review the differences:
   ```bash
   python tests/regression/update_expected_outputs.py --review
   ```

2. Update expected outputs if changes are correct:
   ```bash
   python tests/regression/update_expected_outputs.py --update-all
   ```

For detailed information, see [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md).