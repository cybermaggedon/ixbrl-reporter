# Regression Test Migration Guide

## Overview

The legacy regression tests in the `test/` directory have been integrated into the pytest framework under `tests/regression/`. This provides better error reporting, parallel execution support, and integration with the rest of the test suite.

## Migration Steps

### 1. Install Dependencies

The regression tests require the `ixbrl-parse` package:

```bash
pip install ixbrl-parse
# or install all test dependencies:
pip install -e ".[test]"
```

The tests use the ixbrl-parse library API directly for better performance and integration.

### 2. Running the Tests

#### Run all regression tests:
```bash
pytest tests/regression/ -v
```

#### Run a specific configuration:
```bash
pytest tests/regression/test_ixbrl_regression.py::TestIXBRLRegression::test_ixbrl_generation[unaud-micro.yaml] -v
```

#### Run with parallel execution:
```bash
pytest tests/regression/ -n auto
```

### 3. Updating Expected Outputs

When intentional changes are made that affect report output:

1. Run the legacy script to generate new expected outputs:
   ```bash
   cd test
   ./run_all
   ```

2. Review the differences carefully:
   ```bash
   cd output
   for f in *.kv; do
     echo "=== $f ==="
     diff ../log/$f $f || true
   done
   ```

3. If the changes are correct, update the expected outputs:
   ```bash
   cp output/*.kv log/
   ```

4. Run the pytest regression tests to confirm:
   ```bash
   pytest tests/regression/ -v
   ```

## Key Differences from Legacy Tests

### 1. Better Error Reporting
- Detailed diffs showing exactly what changed
- Line-by-line comparison with context
- Clear test names and failure messages

### 2. Test Markers
- `@pytest.mark.regression` - marks all regression tests
- `@pytest.mark.slow` - marks the comprehensive test that runs all configs

### 3. Parallel Execution
The pytest version supports parallel execution with pytest-xdist:
```bash
pytest tests/regression/ -n 4
```

### 4. Selective Testing
You can run specific test configurations using pytest's parametrization:
```bash
# Run only micro entity tests
pytest tests/regression/ -k "micro" -v
```

### 5. Skip Handling
Tests will automatically skip if:
- `ixbrl-to-kv` is not available
- Expected output files are missing

## Maintaining Both Systems

During the transition period, you may want to maintain both systems:

1. **Legacy system**: Good for generating new expected outputs
2. **Pytest system**: Better for CI/CD and development

To ensure consistency:
- Always update expected outputs using the legacy `run_all` script
- Use pytest for running tests in CI/CD pipelines
- Gradually phase out the legacy scripts once comfortable

## Future Enhancements

Consider these improvements:

1. **Enhanced iXBRL validation**: Extend the ixbrl-parse integration to validate more aspects of the generated reports
2. **Fixtures for test data**: Move test configurations to fixtures for better reusability
3. **Golden file management**: Implement a system for reviewing and approving output changes
4. **Performance benchmarking**: Add timing information to catch performance regressions
5. **Differential testing**: Compare outputs between different versions of the software

## Troubleshooting

### ixbrl-to-kv not found
Install the ixbrl-parse package:
```bash
pip install ixbrl-parse
```

### Tests pass locally but fail in CI
Check that:
1. The same version of ixbrl-parse is installed
2. The working directory is correct (tests assume project root)
3. All required files are committed (configs, expected outputs)

### Differences in version fields
The tests automatically filter out version-related fields that change between runs:
- `VersionProductionSoftware`
- `VersionOfProductionSoftware`

If other fields need filtering, update the `EXCLUDE_FIELDS` list in the test file.