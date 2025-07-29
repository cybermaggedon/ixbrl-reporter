# Regression Test Integration Summary

## Overview

The existing regression tests from the `test/` directory have been successfully integrated into the modern pytest framework under `tests/regression/`. This integration preserves the valuable test coverage while providing better tooling and maintainability.

## Key Features

### 1. **Dual-Mode Operation**
- Legacy shell scripts remain functional for generating expected outputs
- New pytest integration for CI/CD and development workflows

### 2. **Library API Integration**
- Uses `ixbrl-parse` Python API directly for better performance
- Fallback to command-line tool if library unavailable
- Consistent with the original `ixbrl-to-kv` output format

### 3. **Comprehensive Test Coverage**
Tests 15 different report configurations:
- Unaudited reports (micro, abridged, full)
- Audited reports (micro, small, full)
- Revised versions of all report types
- Corporation tax reports
- ESEF and ESEF-FR reports

### 4. **Helper Tools**
- `update_expected_outputs.py`: Interactive tool for reviewing and updating expected outputs
- Detailed diff output for easy comparison
- Batch update capabilities

## Usage

### Running Tests
```bash
# All regression tests
pytest tests/regression/ -v

# Specific configuration
pytest tests/regression/ -k "unaud-micro" -v

# With parallel execution
pytest tests/regression/ -n auto

# Skip slow tests
pytest -m "not slow"
```

### Updating Expected Outputs
```bash
# Review differences
python tests/regression/update_expected_outputs.py --review

# Update all outputs
python tests/regression/update_expected_outputs.py --update-all

# Update specific configs
python tests/regression/update_expected_outputs.py -c unaud-micro aud-full
```

## Benefits

1. **Better Error Reporting**: Detailed diffs showing exactly what changed
2. **Parallel Execution**: Run tests faster with pytest-xdist
3. **Integration**: Works seamlessly with existing pytest infrastructure
4. **Flexibility**: Can run specific tests or configurations
5. **CI/CD Ready**: Proper exit codes and test reporting

## Migration Path

1. **Current State**: Both systems coexist peacefully
2. **Transition Period**: Use legacy for updates, pytest for testing
3. **Future**: Gradual deprecation of shell scripts

## Technical Details

### Test Structure
```python
@pytest.mark.parametrize("config_file", REGRESSION_TEST_CONFIGS)
def test_ixbrl_generation(self, config_file, ...):
    # 1. Generate iXBRL report
    # 2. Parse using ixbrl-parse library
    # 3. Extract and sort key-value pairs
    # 4. Compare against expected output
```

### Key-Value Extraction
```python
# Direct library usage
from ixbrl_parse.ixbrl import parse
tree = ET.parse(html_path)
ixbrl_doc = parse(tree)
data = ixbrl_doc.to_dict()
# Flatten to key|value format
```

### Excluded Fields
- `VersionProductionSoftware`
- `VersionOfProductionSoftware`

These fields change between runs and are automatically filtered out.

## Next Steps

1. Monitor test execution times and optimize if needed
2. Consider adding more validation beyond key-value comparison
3. Implement automated baseline updates for approved changes
4. Add performance regression tracking

The regression test integration ensures that the ixbrl-reporter maintains consistency and reliability while modernizing its testing infrastructure.