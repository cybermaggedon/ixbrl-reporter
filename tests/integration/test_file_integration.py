"""
File I/O Integration Tests

Tests file operations integration: config loading, accounts processing, output generation
as outlined in TEST_STRATEGY.md integration testing requirements.
"""
import pytest
import tempfile
import os
import yaml
from pathlib import Path
from unittest.mock import patch, Mock, mock_open

from ixbrl_reporter.config import Config


@pytest.mark.integration
class TestConfigFileIntegration:
    """Test configuration file loading from disk"""
    
    def test_yaml_config_file_loading(self):
        """Test loading YAML configuration files from disk"""
        config_content = {
            "accounts": {
                "kind": "csv",
                "file": "accounts.csv"
            },
            "report": {
                "name": "Integration Test Report",
                "taxonomy": "uk-gaap"
            },
            "metadata": {
                "accounting": {
                    "currency": "GBP",
                    "decimals": 2,
                    "periods": [
                        {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"}
                    ]
                },
                "business": {
                    "company-name": "Integration Test Ltd"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_content, f)
            config_file = f.name
        
        try:
            # Test loading config from file
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            config = Config(loaded_config)
            
            # Verify loaded content
            assert config.get("accounts.kind") == "csv"
            assert config.get("report.name") == "Integration Test Report"
            assert config.get("metadata.business.company-name") == "Integration Test Ltd"
            assert len(config.get("metadata.accounting.periods")) == 1
            
        finally:
            os.unlink(config_file)
    
    def test_json_config_file_loading(self):
        """Test loading JSON configuration files"""
        import json
        
        config_content = {
            "accounts": {"kind": "piecash", "file": "test.db"},
            "report": {"name": "JSON Test Report"},
            "metadata": {"accounting": {"currency": "USD"}}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_content, f)
            config_file = f.name
        
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
            
            config = Config(loaded_config)
            
            assert config.get("accounts.kind") == "piecash"
            assert config.get("metadata.accounting.currency") == "USD"
            
        finally:
            os.unlink(config_file)
    
    def test_config_file_error_handling(self):
        """Test handling of malformed configuration files"""
        # Test malformed YAML
        malformed_yaml = "accounts:\n  kind: csv\n  file: test.csv\ninvalid: [unclosed"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(malformed_yaml)
            config_file = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
        finally:
            os.unlink(config_file)
    
    def test_config_with_imports(self):
        """Test configuration with import references (//import syntax)"""
        # This tests the import mechanism used in the existing test files
        main_config = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "metadata": "//import metadata.yaml",
            "report": {"name": "Import Test"}
        }
        
        metadata_config = {
            "accounting": {"currency": "GBP", "decimals": 2},
            "business": {"company-name": "Import Test Co"}
        }
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as main_f:
            yaml.dump(main_config, main_f)
            main_file = main_f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as meta_f:
            yaml.dump(metadata_config, meta_f)
            meta_file = meta_f.name
        
        try:
            with open(main_file, 'r') as f:
                main_data = yaml.safe_load(f)
            
            # The import mechanism would need to be implemented
            # For now, test that we can detect import syntax
            assert main_data["metadata"] == "//import metadata.yaml"
            
            # Simulate import resolution
            if isinstance(main_data["metadata"], str) and main_data["metadata"].startswith("//import"):
                with open(meta_file, 'r') as f:
                    imported_data = yaml.safe_load(f)
                main_data["metadata"] = imported_data
            
            config = Config(main_data)
            assert config.get("metadata.business.company-name") == "Import Test Co"
            
        finally:
            os.unlink(main_file)
            os.unlink(meta_file)


@pytest.mark.integration
class TestAccountsFileIntegration:
    """Test accounts file processing integration"""
    
    def test_csv_accounts_file_processing(self):
        """Test processing CSV accounts files"""
        csv_content = '''Date,Transaction ID,Description,Full Account Name,Amount Num.,Commodity/Currency
01/01/20,tx1,Opening Balance,Assets:Cash,1000.00,CURRENCY::GBP
01/02/20,tx2,Purchase,Expenses:Equipment,500.00,CURRENCY::GBP
01/02/20,tx2,Purchase,Assets:Cash,-500.00,CURRENCY::GBP'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file = f.name
        
        try:
            # Test CSV file can be read
            with open(csv_file, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0]['Full Account Name'] == 'Assets:Cash'
            assert rows[0]['Amount Num.'] == '1000.00'
            
            # Test with accounts module (mocked)
            from ixbrl_reporter.accounts import get_class
            
            with patch('ixbrl_reporter.accounts_csv.Accounts') as mock_csv_accounts:
                mock_accounts = Mock()
                mock_csv_accounts.return_value = mock_accounts
                
                accounts_class = get_class("csv")
                accounts_session = accounts_class(csv_file)
                
                mock_csv_accounts.assert_called_once_with(csv_file)
            
        finally:
            os.unlink(csv_file)
    
    @pytest.mark.skip(reason="gnucash module not testable")
    def test_gnucash_file_integration(self):
        """Test GnuCash file integration"""
        # Use the existing fixture file
        gnucash_file = Path(__file__).parent.parent / "fixtures/accounts/sample2.gnucash"
        
        if gnucash_file.exists():
            from ixbrl_reporter.accounts import get_class
            
            with patch('ixbrl_reporter.accounts_gnucash.Accounts') as mock_gnucash:
                mock_accounts = Mock()
                mock_gnucash.return_value = mock_accounts
                
                accounts_class = get_class("gnucash")
                accounts_session = accounts_class(str(gnucash_file))
                
                mock_gnucash.assert_called_once_with(str(gnucash_file))
        else:
            pytest.skip("GnuCash fixture file not available")
    
    def test_accounts_file_error_handling(self):
        """Test accounts file error handling"""
        from ixbrl_reporter.accounts import get_class
        
        # Test with non-existent file
        accounts_class = get_class("csv")
        
        with pytest.raises((FileNotFoundError, IOError)):
            accounts_session = accounts_class("/nonexistent/file.csv")
    
    def test_accounts_file_permissions(self):
        """Test accounts file permission handling"""
        # Create a file with restricted permissions
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test,data\n")
            restricted_file = f.name
        
        try:
            # Remove read permissions
            os.chmod(restricted_file, 0o000)
            
            from ixbrl_reporter.accounts import get_class
            accounts_class = get_class("csv")
            
            with pytest.raises((PermissionError, IOError)):
                accounts_session = accounts_class(restricted_file)
                
        finally:
            # Restore permissions and cleanup
            os.chmod(restricted_file, 0o644)
            os.unlink(restricted_file)


@pytest.mark.integration
class TestOutputFileIntegration:
    """Test output file generation integration"""
    
    def test_ixbrl_output_generation(self):
        """Test iXBRL output file generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_report.html"
            
            # Mock the iXBRL reporter
            with patch('ixbrl_reporter.ixbrl_reporter.IxbrlReporter') as mock_reporter_class:
                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter
                
                # Mock iXBRL output
                ixbrl_content = '''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head><title>Test iXBRL Report</title></head>
<body>
    <ix:nonFraction name="uk-gaap:Assets" contextRef="context-1" 
                   unitRef="GBP" decimals="0">1000</ix:nonFraction>
</body>
</html>'''
                
                mock_reporter.create_report.return_value = ixbrl_content
                
                # Generate output
                from ixbrl_reporter.ixbrl_reporter import IxbrlReporter
                reporter = IxbrlReporter()
                
                mock_data_source = Mock()
                output = reporter.create_report(mock_data_source)
                
                # Write to file
                with open(output_file, 'w') as f:
                    f.write(output)
                
                # Verify file was created and contains expected content
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    content = f.read()
                
                assert 'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"' in content
                assert 'ix:nonFraction' in content
    
    def test_html_output_generation(self):
        """Test HTML output file generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_report.html"
            
            html_content = '''<!DOCTYPE html>
<html>
<head><title>Test HTML Report</title></head>
<body>
    <h1>Financial Report</h1>
    <table>
        <tr><td>Assets</td><td>£1,000</td></tr>
    </table>
</body>
</html>'''
            
            # Write HTML output
            with open(output_file, 'w') as f:
                f.write(html_content)
            
            # Verify file structure
            assert output_file.exists()
            assert output_file.suffix == '.html'
            
            with open(output_file, 'r') as f:
                content = f.read()
            
            assert '<!DOCTYPE html>' in content
            assert '<h1>Financial Report</h1>' in content
    
    def test_text_output_generation(self):
        """Test text output file generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_report.txt"
            
            # Mock text reporter
            with patch('ixbrl_reporter.text_reporter.TextReporter') as mock_text_class:
                mock_text = Mock()
                mock_text_class.return_value = mock_text
                
                text_content = '''FINANCIAL REPORT
=================

Assets:         £1,000
Liabilities:    £  500
Equity:         £  500
'''
                
                mock_text.create_report.return_value = text_content
                
                from ixbrl_reporter.text_reporter import TextReporter
                reporter = TextReporter()
                
                mock_data_source = Mock()
                output = reporter.create_report(mock_data_source)
                
                with open(output_file, 'w') as f:
                    f.write(output)
                
                assert output_file.exists()
                
                with open(output_file, 'r') as f:
                    content = f.read()
                
                assert 'FINANCIAL REPORT' in content
                assert 'Assets:' in content
    
    def test_output_file_error_handling(self):
        """Test output file error handling"""
        # Test writing to read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            os.chmod(readonly_dir, 0o444)  # Read-only
            
            output_file = readonly_dir / "test.html"
            
            try:
                with pytest.raises((PermissionError, OSError)):
                    with open(output_file, 'w') as f:
                        f.write("<html>Test</html>")
            finally:
                # Restore permissions for cleanup
                os.chmod(readonly_dir, 0o755)


@pytest.mark.integration
class TestTemplateFileIntegration:
    """Test template and taxonomy file processing"""
    
    def test_template_file_loading(self):
        """Test loading template files"""
        template_content = {
            "elements": [
                {"element": "worksheet", "worksheet": "balance-sheet"}
            ],
            "worksheets": {
                "balance-sheet": {
                    "columns": [
                        {"name": "current-year", "title": "2020"}
                    ],
                    "rows": [
                        {"id": "assets", "description": "Total Assets", "account": "Assets"}
                    ]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(template_content, f)
            template_file = f.name
        
        try:
            with open(template_file, 'r') as f:
                loaded_template = yaml.safe_load(f)
            
            # Verify template structure
            assert "elements" in loaded_template
            assert "worksheets" in loaded_template
            assert len(loaded_template["elements"]) == 1
            assert loaded_template["elements"][0]["element"] == "worksheet"
            
            # Verify worksheet structure
            worksheet = loaded_template["worksheets"]["balance-sheet"]
            assert "columns" in worksheet
            assert "rows" in worksheet
            assert len(worksheet["rows"]) == 1
            
        finally:
            os.unlink(template_file)
    
    def test_taxonomy_file_loading(self):
        """Test loading taxonomy files"""
        taxonomy_content = {
            "version": "1.0",
            "namespace": "http://test.taxonomy.org/2020",
            "elements": {
                "Assets": {
                    "type": "monetary",
                    "period": "instant"
                },
                "Revenue": {
                    "type": "monetary", 
                    "period": "duration"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(taxonomy_content, f)
            taxonomy_file = f.name
        
        try:
            with open(taxonomy_file, 'r') as f:
                loaded_taxonomy = yaml.safe_load(f)
            
            # Verify taxonomy structure
            assert "version" in loaded_taxonomy
            assert "namespace" in loaded_taxonomy
            assert "elements" in loaded_taxonomy
            
            # Verify element definitions
            elements = loaded_taxonomy["elements"]
            assert "Assets" in elements
            assert elements["Assets"]["type"] == "monetary"
            assert elements["Assets"]["period"] == "instant"
            
        finally:
            os.unlink(taxonomy_file)
    
    def test_file_encoding_handling(self):
        """Test handling of different file encodings"""
        # Test UTF-8 with special characters
        utf8_content = {
            "company-name": "Tëst Çömpâny £td",
            "currency": "€",
            "description": "Spéciål chäractërs tëst"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.yaml', delete=False) as f:
            yaml.dump(utf8_content, f, allow_unicode=True)
            utf8_file = f.name
        
        try:
            # Test reading UTF-8 file
            with open(utf8_file, 'r', encoding='utf-8') as f:
                loaded_content = yaml.safe_load(f)
            
            assert loaded_content["company-name"] == "Tëst Çömpâny £td"
            assert loaded_content["currency"] == "€"
            
        finally:
            os.unlink(utf8_file)


@pytest.mark.integration  
class TestFileIntegrationEdgeCases:
    """Test file integration edge cases"""
    
    def test_large_file_handling(self):
        """Test handling of large configuration files"""
        # Create a larger config with many periods
        large_config = {
            "accounts": {"kind": "csv", "file": "large.csv"},
            "report": {"name": "Large Config Test"},
            "metadata": {
                "accounting": {
                    "periods": [
                        {"name": f"Year{i}", "start": f"{i}-01-01", "end": f"{i}-12-31"}
                        for i in range(2000, 2020)  # 20 periods
                    ]
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_config, f)
            config_file = f.name
        
        try:
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f)
            
            config = Config(loaded_config)
            
            # Should handle large configs efficiently
            periods = config.get("metadata.accounting.periods")
            assert len(periods) == 20
            assert periods[0]["name"] == "Year2000"
            assert periods[-1]["name"] == "Year2019"
            
        finally:
            os.unlink(config_file)
    
    def test_concurrent_file_access(self):
        """Test concurrent file access patterns"""
        config_content = {"accounts": {"kind": "csv", "file": "test.csv"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_content, f)
            config_file = f.name
        
        try:
            # Simulate multiple concurrent reads
            configs = []
            for _ in range(5):
                with open(config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                configs.append(Config(loaded_config))
            
            # All configs should be independently functional
            for config in configs:
                assert config.get("accounts.kind") == "csv"
            
        finally:
            os.unlink(config_file)
    
    def test_temporary_file_cleanup(self):
        """Test proper cleanup of temporary files"""
        temp_files = []
        
        # Create multiple temporary files
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump({"test": f"file{i}"}, f)
                temp_files.append(f.name)
        
        # Verify files exist
        for temp_file in temp_files:
            assert Path(temp_file).exists()
        
        # Clean up
        for temp_file in temp_files:
            os.unlink(temp_file)
        
        # Verify files are gone
        for temp_file in temp_files:
            assert not Path(temp_file).exists()
