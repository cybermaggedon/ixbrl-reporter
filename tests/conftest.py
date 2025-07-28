"""
Shared fixtures for ixbrl-reporter tests
"""
import pytest
import yaml
from pathlib import Path


@pytest.fixture
def sample_config_data():
    """Basic configuration data for testing"""
    return {
        "accounts": {"kind": "csv", "file": "test.csv"},
        "report": {"name": "Test Report", "taxonomy": "basic"},
        "nested": {"deep": {"value": 42}}
    }


@pytest.fixture
def temp_config_file(tmp_path, sample_config_data):
    """Create a temporary YAML config file"""
    config_file = tmp_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config_data, f)
    return str(config_file)


@pytest.fixture
def invalid_yaml_file(tmp_path):
    """Create a temporary file with invalid YAML"""
    invalid_file = tmp_path / "invalid.yaml"
    with open(invalid_file, 'w') as f:
        f.write("invalid: yaml: content: [\n")
    return str(invalid_file)


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content as string"""
    return """
accounts:
  kind: csv
  file: test.csv
report:
  name: Test Report
  taxonomy: basic
"""


@pytest.fixture
def fixtures_path():
    """Path to test fixtures directory"""
    return Path(__file__).parent / "fixtures"