# Test Strategy for ixbrl-reporter

## Overview

This document outlines the testing strategy for the ixbrl-reporter project, which generates iXBRL reports from templates and accounts files. The testing approach focuses on three layers: unit tests, integration tests, and contract tests to ensure reliability and maintainability.

## Current Testing State

The project currently has:
- **Integration-style tests** in `/test/` directory with YAML configuration files
- **Shell-based test runner** (`test/run`) that compares generated output with expected results
- **No formal unit test framework** - we need to add pytest-based testing

## Testing Architecture

### 1. Unit Tests (`tests/unit/`)

Test individual components in isolation with mocked dependencies.

#### Core Components to Test:

**Configuration Management (`test_config.py`)**
- `Config.load()` - YAML/JSON parsing
- `Config.get()` - Path navigation (`"part1.part2.part3"`)
- `Config.set()` - Value setting
- `Config.resolve_refs()` - Reference resolution
- Error handling for malformed config files

**Accounts Abstraction (`test_accounts.py`)**
- `get_class()` - Factory method for different account types
- Account type detection (gnucash, piecash, csv)
- Error handling for unknown account types

**Data Source (`test_data_source.py`)**
- `DataSource.__init__()` - Initialization with config and session
- `DataSource.get_element()` - Element retrieval
- Period handling and context management
- Value set operations

**Element System (`test_element.py`)**
- `Element.load()` - Factory method for different element types
- Element type detection (composite, worksheet, notes, etc.)
- Element rendering pipeline

**Taxonomy Management (`test_taxonomy.py`)**
- Taxonomy loading and validation
- Fact creation (StringFact, DateFact, MoneyFact, etc.)
- Dimension handling (NamedDimension, TypedDimension)
- Context generation

**CLI Interface (`test_main.py`)**
- Argument parsing and validation
- Version retrieval from package metadata
- Output format handling (ixbrl, html, text, debug)
- Error handling and user feedback

#### Test Utilities:
```python
# tests/conftest.py
@pytest.fixture
def sample_config():
    return Config({
        "accounts": {"kind": "csv", "file": "test.csv"},
        "report": {"taxonomy": "test-taxonomy.yaml"}
    })

@pytest.fixture
def mock_accounts_session():
    # Mock accounts session for testing
    pass
```

### 2. Integration Tests (`tests/integration/`)

Test component interactions with realistic data and configurations.

**End-to-End Workflow (`test_e2e_workflow.py`)**
- Load config → Create accounts session → Generate DataSource → Produce output
- Test with different account backends (CSV, GnuCash, Piecash)
- Validate output formats (iXBRL, HTML, text, debug)

**File I/O Integration (`test_file_integration.py`)**
- Configuration file loading from disk
- Accounts file processing
- Output file generation
- Template and taxonomy file processing

**Report Generation (`test_report_generation.py`)**
- Full report generation pipeline
- Different report types (audited, unaudited, micro, small, full)
- Template processing and variable substitution

### 3. Contract Tests (`tests/contract/`)

Ensure compatibility with external systems and data formats.

**Data Format Contracts (`test_data_contracts.py`)**
- GnuCash file format compatibility
- CSV format requirements and validation
- YAML configuration schema validation

**iXBRL Output Contracts (`test_ixbrl_contracts.py`)**
- Valid iXBRL output generation
- Compliance with iXBRL standards
- Taxonomy adherence
- XML schema validation

**Template Contracts (`test_template_contracts.py`)**
- Template syntax and structure validation
- Required template elements
- Variable substitution contracts

## Test Data Management

### Test Fixtures (`tests/fixtures/`)
```
tests/fixtures/
├── configs/
│   ├── minimal.yaml
│   ├── full-featured.yaml
│   └── invalid-configs/
├── accounts/
│   ├── sample.csv
│   ├── sample.gnucash
│   └── edge-cases/
├── templates/
│   ├── basic-report.yaml
│   └── complex-report.yaml
└── expected-outputs/
    ├── sample-report.ixbrl
    └── sample-report.html
```

### Data Generation
- **Synthetic test data** for predictable testing
- **Anonymized real data** for realistic scenarios
- **Edge case data** for boundary testing

## Testing Tools and Configuration

### Dependencies
```toml
# Add to pyproject.toml [project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.10",
    "pytest-xdist>=3.0",  # parallel testing
    "lxml>=4.0",          # XML validation
    "pyyaml>=6.0",        # YAML processing
]
```

### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --cov=ixbrl_reporter
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests  
    contract: Contract tests
    slow: Slow running tests
```

## Test Execution Strategy

### Local Development
```bash
# Run all tests
pytest

# Run by category
pytest -m unit
pytest -m integration
pytest -m contract

# Run with coverage
pytest --cov=ixbrl_reporter --cov-report=html

# Run in parallel
pytest -n auto
```

### CI/CD Pipeline
1. **Fast feedback** - Unit tests first (< 30 seconds)
2. **Integration tests** - With test data (< 2 minutes)
3. **Contract tests** - Full validation (< 5 minutes)
4. **Coverage reporting** - Minimum 80% coverage
5. **Performance regression** - Compare with baseline

## Mock Strategy

### External Dependencies
- **File system operations** - Mock file I/O for unit tests
- **Account backends** - Mock GnuCash/Piecash sessions
- **XML/YAML parsers** - Mock for error condition testing
- **Package metadata** - Mock version retrieval

### Internal Dependencies
- **DataSource** - Mock for element testing
- **Taxonomy** - Mock for rendering testing
- **Config** - Mock for component isolation

## Performance Testing

### Benchmarks (`tests/performance/`)
- **Large file processing** - Memory usage and time
- **Complex report generation** - Rendering performance
- **Concurrent processing** - Multi-threading safety

### Regression Testing
- **Baseline measurements** - Track performance over time
- **Memory profiling** - Detect memory leaks
- **CPU profiling** - Identify bottlenecks

## Error Scenarios

### Input Validation
- **Malformed configuration files**
- **Missing required fields**
- **Invalid account file formats**
- **Corrupted template files**

### Runtime Errors
- **Network timeouts** (if applicable)
- **File permission issues**
- **Memory constraints**
- **Invalid data transformations**

## Regression Tests (`tests/regression/`)

### Overview
The project includes comprehensive regression tests that verify iXBRL report generation remains consistent across changes. These tests use real-world configurations and compare outputs against known good results.

**Regression Test Framework (`test_ixbrl_regression.py`)**
- Runs ixbrl-reporter on 15 different report configurations
- Extracts key-value pairs using `ixbrl-to-kv` tool
- Compares against expected outputs in `/log/` directory
- Filters out version-related fields that change between runs

**Test Configurations Include:**
- Audited/Unaudited reports (micro, small, full, abridged)
- Revised/Non-revised versions
- Corporation tax reports
- ESEF and ESEF-FR reports

**Helper Tools:**
- `update_expected_outputs.py` - Script to review and update expected outputs
- `MIGRATION_GUIDE.md` - Documentation for transitioning from legacy tests

### Running Regression Tests
```bash
# Run all regression tests
pytest tests/regression/ -v

# Run specific configuration
pytest tests/regression/ -k "unaud-micro" -v

# Run in parallel
pytest tests/regression/ -n auto

# Update expected outputs after intentional changes
python tests/regression/update_expected_outputs.py --review
```

## Migration from Current Tests

### Phase 1: Preserve Existing ✓ (Completed)
1. Keep current `/test/` directory and shell scripts
2. Add pytest infrastructure alongside
3. Ensure both systems can coexist

### Phase 2: Pytest Implementation ✓ (Completed)
1. Implement unit tests for core components
2. Convert shell-based integration tests to pytest
3. Add contract tests for data formats
4. Integrate regression tests into pytest framework

### Phase 3: Consolidation
1. Migrate all test data to `/tests/fixtures/`
2. Gradually phase out shell-based test system
3. Full pytest adoption while maintaining backwards compatibility

## Success Metrics

- **Code Coverage**: Minimum 80% line coverage
- **Test Performance**: Full test suite < 5 minutes
- **Reliability**: Tests pass consistently across environments
- **Maintainability**: Easy to add tests for new features
- **Documentation**: Clear test intentions and setup

## Implementation Priority

1. **High Priority**: Unit tests for Config, accounts, main CLI
2. **Medium Priority**: Integration tests for report generation
3. **Low Priority**: Contract tests and performance benchmarks

This strategy provides a structured approach to testing that balances thoroughness with maintainability, ensuring the ixbrl-reporter remains reliable as it evolves.