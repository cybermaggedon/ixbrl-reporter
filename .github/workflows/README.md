# GitHub Actions Workflows

This directory contains the CI/CD workflows for the ixbrl-reporter project.

## Workflows

### 1. Continuous Integration (`ci.yaml`)
- **Trigger**: Push to master branch
- **Purpose**: Main CI pipeline with comprehensive testing
- **Tests Run**:
  - Unit tests with coverage reporting
  - Contract tests
  - Integration tests
  - Regression tests (excluding slow tests)
  - Type checking with mypy
  - CLI script testing
- **Coverage**: Uploaded to Codecov

### 2. Pull Request Testing (`pull-request.yaml`)
- **Trigger**: Pull requests and pushes to master
- **Purpose**: Validate changes before merging
- **Matrix Testing**: Python 3.12 and 3.13
- **Tests Run**:
  - Unit tests
  - Contract tests
  - Integration tests
  - Regression tests (excluding slow tests)
  - Type checking
  - Package installation verification

### 3. Regression Tests (`regression-tests.yaml`)
- **Trigger**: 
  - Manual workflow dispatch
  - Weekly schedule (Sundays at 2 AM UTC)
  - Changes to test data or core functionality
- **Purpose**: Comprehensive regression testing
- **Matrix Testing**: Python 3.11 and 3.12
- **Features**:
  - Full regression test suite including slow tests
  - Legacy test compatibility verification
  - Test artifact upload for debugging
  - Summary job for overall status

## Test Categories

### Unit Tests
- Fast, isolated tests for individual components
- Run on every push and PR
- Coverage reporting enabled

### Integration Tests
- Test component interactions
- Verify file I/O and workflows
- Run on every push and PR

### Contract Tests
- Validate data formats and interfaces
- Ensure compatibility with external systems
- Run on every push and PR

### Regression Tests
- Compare generated reports against known good outputs
- 15 different report configurations
- Fast tests run on every push
- Complete suite runs weekly or on demand

## Running Workflows Locally

To test workflows locally before pushing:

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash  # Linux

# Run a specific workflow
act -W .github/workflows/ci.yaml

# Run with specific Python version
act -W .github/workflows/pull-request.yaml --matrix python-version:3.12
```

## Workflow Maintenance

### Adding New Tests
1. Add test files to appropriate directory under `tests/`
2. Tests will automatically be picked up by existing workflows
3. Use appropriate pytest markers (@pytest.mark.slow for long-running tests)

### Updating Python Versions
1. Update the `python-version` in workflow files
2. Ensure compatibility with new versions
3. Update matrix testing configurations

### Modifying Test Dependencies
1. Update `requirements-dev.txt`
2. Update `pyproject.toml` test dependencies if needed
3. Clear GitHub Actions cache if dependency issues occur

## Troubleshooting

### Common Issues

1. **Regression tests fail after intentional changes**
   - Review changes with: `python tests/regression/update_expected_outputs.py --review`
   - Update if correct: `python tests/regression/update_expected_outputs.py --update-all`

2. **Type checking failures**
   - Ensure type hints are correct
   - Update mypy configuration if needed

3. **Coverage drops below threshold**
   - Add tests for uncovered code
   - Update coverage threshold if justified

### Debugging Failed Workflows

1. Check the workflow logs in GitHub Actions tab
2. Download test artifacts for regression test failures
3. Run tests locally to reproduce issues
4. Use `pytest -vvs` for verbose output

## Best Practices

1. **Keep workflows DRY**: Use composite actions for repeated steps
2. **Cache dependencies**: Speeds up workflow execution
3. **Matrix testing**: Test against multiple Python versions
4. **Fail fast**: Stop matrix jobs if one fails
5. **Upload artifacts**: For debugging test failures