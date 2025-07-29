"""
Regression tests for iXBRL report generation

These tests verify that generated iXBRL reports contain the expected data
by comparing key-value extractions against known good outputs.
"""
import os
import subprocess
import pytest
from pathlib import Path
import tempfile
import difflib
from typing import List, Tuple


# Define test cases from the legacy run_all script
REGRESSION_TEST_CONFIGS = [
    "unaud-micro-rev.yaml",
    "unaud-micro.yaml",
    "aud-micro.yaml",
    "aud-micro-rev.yaml",
    "aud-small.yaml",
    "aud-small-rev.yaml",
    "unaud-abr.yaml",
    "unaud-abr-rev.yaml",
    "unaud-full.yaml",
    "unaud-full-rev.yaml",
    "aud-full.yaml",
    "aud-full-rev.yaml",
    "ct.yaml",
    "esef.yaml",
    "esef-fr.yaml"
]

# Fields to exclude from comparison (version info that changes between runs)
EXCLUDE_FIELDS = [
    'VersionProductionSoftware',
    'VersionOfProductionSoftware'
]


# Module-level fixtures that can be used by all test classes
@pytest.fixture(scope="module")
def project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def test_configs_dir(project_root):
    """Directory containing test configuration files"""
    return project_root / "test"


@pytest.fixture(scope="module")
def expected_outputs_dir(project_root):
    """Directory containing expected KV outputs"""
    return project_root / "log"


@pytest.fixture(scope="module")
def ixbrl_to_kv_available():
    """Check if ixbrl-to-kv is available"""
    try:
        subprocess.run(["ixbrl-to-kv", "--help"], 
                     capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class TestIXBRLRegression:
    """Test suite for iXBRL report generation regression tests"""
    
    def extract_kv_pairs(self, html_path: Path, 
                        ixbrl_to_kv_available: bool) -> List[str]:
        """Extract key-value pairs from iXBRL HTML
        
        Args:
            html_path: Path to the generated HTML file
            ixbrl_to_kv_available: Whether ixbrl-to-kv command is available
            
        Returns:
            List of key-value pairs as strings
        """
        try:
            # Use the ixbrl-parse library directly
            from lxml import etree as ET
            from ixbrl_parse.ixbrl import parse
            
            # Parse the iXBRL file
            tree = ET.parse(str(html_path))
            ixbrl_doc = parse(tree)
            
            # Convert to dictionary and flatten to key-value pairs
            data = ixbrl_doc.to_dict()
            lines = []
            
            def flatten_dict(d, prefix=[]):
                """Recursively flatten nested dictionary to key-value pairs"""
                for k, v in d.items():
                    key = prefix + [k]
                    if isinstance(v, dict):
                        flatten_dict(v, key)
                    else:
                        # Format as key|value to match expected output format
                        lines.append(f"{'.'.join(key)}|{str(v)[:40]}")
            
            flatten_dict(data)
            
        except ImportError:
            # Fallback to command-line tool if library not available
            if ixbrl_to_kv_available:
                result = subprocess.run(
                    ["ixbrl-to-kv", str(html_path)],
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split('\n')
            else:
                pytest.skip("ixbrl-parse library not available, install with: pip install ixbrl-parse")
        
        # Filter out excluded fields and sort
        filtered_lines = [
            line for line in lines
            if line and not any(exclude in line for exclude in EXCLUDE_FIELDS)
        ]
        return sorted(filtered_lines)
    
    def compare_outputs(self, actual: List[str], expected: List[str],
                       config_name: str) -> None:
        """Compare actual vs expected outputs
        
        Args:
            actual: Actual KV pairs
            expected: Expected KV pairs
            config_name: Name of the test config for error messages
        """
        if actual != expected:
            # Generate a detailed diff for debugging
            diff = list(difflib.unified_diff(
                expected,
                actual,
                fromfile=f"expected ({config_name})",
                tofile=f"actual ({config_name})",
                lineterm=""
            ))
            
            # Format the diff nicely
            diff_str = '\n'.join(diff)
            pytest.fail(f"Output mismatch for {config_name}:\n{diff_str}")
    
    @pytest.mark.parametrize("config_file", REGRESSION_TEST_CONFIGS)
    def test_ixbrl_generation(self, config_file, project_root, 
                             test_configs_dir, expected_outputs_dir,
                             ixbrl_to_kv_available):
        """Test iXBRL generation for each configuration
        
        This test:
        1. Generates an iXBRL report from a YAML config
        2. Extracts key-value pairs
        3. Compares against expected output
        """
        config_path = test_configs_dir / config_file
        expected_kv_file = expected_outputs_dir / f"{config_file[:-5]}.kv"
        
        # Skip if expected output doesn't exist
        if not expected_kv_file.exists():
            pytest.skip(f"Expected output {expected_kv_file} not found")
        
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / f"{config_file[:-5]}.html"
            
            # Generate the report
            cmd = [
                "ixbrl-reporter",
                str(config_path),
                "report",
                "ixbrl"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            
            # Check that the command succeeded
            assert result.returncode == 0, \
                f"Report generation failed: {result.stderr}"
            
            # Write output to file
            output_path.write_text(result.stdout)
            
            # Extract KV pairs
            actual_kv = self.extract_kv_pairs(output_path, 
                                            ixbrl_to_kv_available)
            
            # Load expected KV pairs
            expected_lines = expected_kv_file.read_text().strip().split('\n')
            expected_kv = sorted([
                line for line in expected_lines
                if not any(exclude in line for exclude in EXCLUDE_FIELDS)
            ])
            
            # Compare
            self.compare_outputs(actual_kv, expected_kv, config_file)
    
    def test_all_regression_configs(self, project_root, test_configs_dir, 
                                   expected_outputs_dir, ixbrl_to_kv_available):
        """Run all regression tests and provide a summary
        
        This is similar to the run_all script but provides better
        error reporting and integration with pytest.
        """
        failures = []
        
        for config_file in REGRESSION_TEST_CONFIGS:
            try:
                self.test_ixbrl_generation(
                    config_file, project_root, test_configs_dir,
                    expected_outputs_dir, ixbrl_to_kv_available
                )
            except (AssertionError, pytest.skip.Exception) as e:
                failures.append((config_file, str(e)))
        
        if failures:
            failure_msg = "Regression test failures:\n"
            for config, error in failures:
                failure_msg += f"\n{config}: {error}"
            pytest.fail(failure_msg)


@pytest.mark.regression
class TestRegressionDataIntegrity:
    """Tests to ensure regression test data is valid and complete"""
    
    def test_all_configs_have_expected_outputs(self, project_root):
        """Verify all config files have corresponding expected outputs"""
        test_dir = project_root / "test"
        log_dir = project_root / "log"
        
        missing_outputs = []
        
        for config in REGRESSION_TEST_CONFIGS:
            config_path = test_dir / config
            expected_kv = log_dir / f"{config[:-5]}.kv"
            
            if config_path.exists() and not expected_kv.exists():
                missing_outputs.append(config)
        
        assert not missing_outputs, \
            f"Missing expected outputs for: {', '.join(missing_outputs)}"
    
    def test_no_orphaned_expected_outputs(self, project_root):
        """Verify no expected outputs without corresponding configs"""
        test_dir = project_root / "test" 
        log_dir = project_root / "log"
        
        orphaned = []
        
        for kv_file in log_dir.glob("*.kv"):
            config_name = f"{kv_file.stem}.yaml"
            if config_name not in REGRESSION_TEST_CONFIGS:
                orphaned.append(kv_file.name)
        
        assert not orphaned, \
            f"Orphaned expected outputs: {', '.join(orphaned)}"
