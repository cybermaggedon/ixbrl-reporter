# Unit Test Implementation Plan

## Overview

This plan outlines the step-by-step implementation of unit tests for ixbrl-reporter, starting with the most foundational components and building up systematically.

## Phase 1: Infrastructure Setup (Priority: High)

### 1.1 Update pyproject.toml
Add testing dependencies and configuration:
```toml
[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-cov>=4.0", 
    "pytest-mock>=3.10",
    "pyyaml>=6.0"
]
```

### 1.2 Create Test Directory Structure
```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_accounts.py
│   ├── test_main.py
│   └── test_data_source.py
├── fixtures/
│   ├── configs/
│   │   ├── minimal.yaml
│   │   ├── complete.yaml
│   │   └── invalid.yaml
│   └── accounts/
│       └── sample.csv
└── pytest.ini
```

### 1.3 Configure pytest
Create `pytest.ini` with basic configuration:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = --strict-markers --cov=ixbrl_reporter
markers =
    unit: Unit tests
```

**Estimated Time:** 1-2 hours

## Phase 2: Config Module Tests (Priority: High)

### 2.1 Test Scope
The `Config` class is foundational - everything depends on it. Focus on:
- `Config.load()` - YAML file loading
- `Config.get()` - Dotted path navigation  
- `Config.set()` - Value setting
- `Config.resolve_refs()` - Reference resolution
- Error handling

### 2.2 Implementation: `tests/unit/test_config.py`

**Test Categories:**
```python
class TestConfigLoad:
    def test_load_valid_yaml(self)
    def test_load_missing_file(self)
    def test_load_invalid_yaml(self)
    def test_load_with_resolve_false(self)

class TestConfigGet:
    def test_get_simple_key(self)
    def test_get_nested_path(self)
    def test_get_nonexistent_key(self)
    def test_get_with_default(self)

class TestConfigSet:
    def test_set_simple_value(self)
    def test_set_nested_path(self)
    def test_overwrite_existing(self)

class TestConfigResolveRefs:
    def test_resolve_simple_reference(self)
    def test_resolve_nested_references(self)
    def test_resolve_circular_reference(self)
```

**Key Test Fixtures:**
```python
@pytest.fixture
def sample_config_data():
    return {
        "accounts": {"kind": "csv", "file": "test.csv"},
        "report": {"name": "Test Report"},
        "nested": {"deep": {"value": 42}}
    }

@pytest.fixture
def temp_config_file(tmp_path, sample_config_data):
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config_data, f)
    return config_file
```

**Estimated Time:** 4-6 hours

## Phase 3: Accounts Module Tests (Priority: High)

### 3.1 Test Scope
The `accounts` module is a simple factory - perfect for demonstrating testing patterns:
- `get_class()` function
- Support for different account types (gnucash, piecash, csv)
- Error handling for unknown types

### 3.2 Implementation: `tests/unit/test_accounts.py`

**Test Categories:**
```python
class TestGetClass:
    def test_get_gnucash_class(self)
    def test_get_piecash_class(self)  
    def test_get_csv_class(self)
    def test_get_unknown_class_raises_error(self)
    
    @pytest.mark.parametrize("kind,expected_module", [
        ("gnucash", "ixbrl_reporter.accounts_gnucash"),
        ("piecash", "ixbrl_reporter.accounts_piecash"), 
        ("csv", "ixbrl_reporter.accounts_csv")
    ])
    def test_get_class_returns_correct_type(self, kind, expected_module)
```

**Mock Strategy:**
```python
@pytest.fixture
def mock_accounts_modules(mocker):
    # Mock the import statements to avoid dependencies
    mock_gnucash = mocker.patch('ixbrl_reporter.accounts_gnucash')
    mock_piecash = mocker.patch('ixbrl_reporter.accounts_piecash') 
    mock_csv = mocker.patch('ixbrl_reporter.accounts_csv')
    return {
        'gnucash': mock_gnucash,
        'piecash': mock_piecash,
        'csv': mock_csv
    }
```

**Estimated Time:** 2-3 hours

## Phase 4: CLI/Main Module Tests (Priority: High)

### 4.1 Test Scope
The `__main__.py` module is the entry point - critical for user experience:
- `main()` function argument parsing
- Version retrieval from package metadata
- Configuration loading and processing
- Output format dispatch
- Error handling and user feedback

### 4.2 Implementation: `tests/unit/test_main.py`

**Test Categories:**
```python
class TestMain:
    def test_insufficient_args_exits_with_usage(self)
    def test_version_retrieval_success(self)
    def test_version_retrieval_fallback(self) 
    def test_config_loading(self)
    def test_accounts_class_creation(self)
    def test_ixbrl_output_format(self)
    def test_html_output_format(self)
    def test_text_output_format(self)
    def test_debug_output_format(self)
    def test_unknown_output_format_raises_error(self)
    def test_exception_handling_prints_to_stderr(self)

class TestVersionRetrieval:
    def test_version_from_package_metadata(self)
    def test_version_fallback_on_exception(self)
```

**Mock Strategy:**
```python
@pytest.fixture
def mock_dependencies(mocker):
    return {
        'config': mocker.patch('ixbrl_reporter.__main__.Config'),
        'accounts': mocker.patch('ixbrl_reporter.__main__.accounts'),
        'taxonomy': mocker.patch('ixbrl_reporter.__main__.Taxonomy'),
        'data_source': mocker.patch('ixbrl_reporter.__main__.DataSource'),
        'version': mocker.patch('ixbrl_reporter.__main__.version'),
        'sys_argv': mocker.patch('sys.argv'),
        'sys_stderr': mocker.patch('sys.stderr'),
        'sys_stdout': mocker.patch('sys.stdout')
    }
```

**Estimated Time:** 4-5 hours

## Phase 5: Test Fixtures and Utilities (Priority: Medium)

### 5.1 Create Shared Fixtures
**`tests/conftest.py`:**
```python
@pytest.fixture
def sample_config():
    """Minimal valid configuration for testing"""
    
@pytest.fixture  
def temp_config_file(tmp_path):
    """Temporary config file for file I/O tests"""
    
@pytest.fixture
def mock_accounts_session():
    """Mock accounts session for testing"""

@pytest.fixture
def sample_yaml_content():
    """Sample YAML data for configuration tests"""
```

### 5.2 Create Test Data Files
**`tests/fixtures/configs/minimal.yaml`:**
```yaml
accounts:
  kind: csv
  file: test.csv
report:
  name: Test Report
  taxonomy: basic
```

**Estimated Time:** 2-3 hours

## Phase 6: Setup and Configuration (Priority: Medium)

### 6.1 Update pyproject.toml
Add the test configuration and ensure compatibility.

### 6.2 Create Development Scripts
**`scripts/test.sh`:**
```bash
#!/bin/bash
# Run tests with coverage
pytest --cov=ixbrl_reporter --cov-report=html --cov-report=term-missing
```

### 6.3 Documentation Updates
Update README.md with testing instructions.

**Estimated Time:** 1-2 hours

## Implementation Order and Timeline

### Week 1: Foundation
- Day 1-2: Phase 1 (Infrastructure Setup)
- Day 3-4: Phase 2 (Config Tests)
- Day 5: Phase 3 (Accounts Tests)

### Week 2: Core Features  
- Day 1-2: Phase 4 (CLI Tests)
- Day 3: Phase 5 (Fixtures)
- Day 4: Phase 6 (Configuration)
- Day 5: Integration and refinement

## Success Criteria

### Phase Completion Metrics:
- **Phase 1**: `pytest --collect-only` runs without errors
- **Phase 2**: Config module achieves >90% test coverage  
- **Phase 3**: Accounts module achieves >95% test coverage
- **Phase 4**: Main module achieves >80% test coverage
- **Phase 5**: Fixtures support all unit tests
- **Phase 6**: Full test suite runs in <30 seconds

### Overall Success:
- All unit tests pass consistently
- Combined coverage of tested modules >85%
- Test suite provides clear failure messages
- Easy to run: `pytest` or `python -m pytest`

## Next Steps After Unit Tests

Once unit tests are complete, the natural progression is:
1. **Integration Tests** - Test component interactions
2. **Data Source Tests** - More complex business logic
3. **Element System Tests** - Template processing
4. **End-to-End Tests** - Full report generation

## Risk Mitigation

### Potential Issues:
- **External Dependencies**: Mock all file I/O and external libraries
- **Complex Business Logic**: Start simple, add complexity gradually  
- **Test Data Management**: Use fixtures and temporary files
- **Performance**: Keep unit tests fast (<1s each)

### Mitigation Strategies:
- Comprehensive mocking strategy
- Incremental implementation with frequent testing
- Clear separation between unit and integration tests
- Regular refactoring to maintain test quality

This plan provides a clear roadmap for implementing unit tests systematically, ensuring solid foundation before moving to more complex testing scenarios.