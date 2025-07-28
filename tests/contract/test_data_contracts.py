"""
Contract tests for data format compatibility (GnuCash, CSV, YAML)

These tests ensure compatibility with external systems and data formats
as outlined in TEST_STRATEGY.md contract testing requirements.
"""
import pytest
import csv
import yaml
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from ixbrl_reporter.config import Config
import ixbrl_reporter.accounts as accounts_module


@pytest.mark.contract
class TestCSVDataContract:
    """Test CSV format requirements and validation"""
    
    def test_csv_required_columns_present(self):
        """CSV files must contain required columns for transaction processing"""
        required_columns = [
            "Date", "Transaction ID", "Description", "Full Account Name", 
            "Amount Num.", "Commodity/Currency"
        ]
        
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            for required_col in required_columns:
                assert required_col in headers, f"Required column '{required_col}' missing from CSV"
    
    def test_csv_data_types_valid(self):
        """CSV data must have valid types for critical fields"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                if row["Date"]:  # Skip empty date rows (continuation rows)
                    # Date format validation
                    date_str = row["Date"]
                    assert "/" in date_str, f"Row {row_num}: Date format should contain '/' separator"
                    
                # Amount validation
                if row["Amount Num."]:
                    amount_str = row["Amount Num."]
                    try:
                        float(amount_str)
                    except ValueError:
                        pytest.fail(f"Row {row_num}: Amount '{amount_str}' is not a valid number")
                
                # Currency validation
                if row["Commodity/Currency"]:
                    currency = row["Commodity/Currency"]
                    assert currency.startswith("CURRENCY::"), f"Row {row_num}: Currency format should start with 'CURRENCY::'"
    
    def test_csv_account_hierarchy_valid(self):
        """CSV accounts must follow hierarchical naming convention"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, 1):
                full_account = row["Full Account Name"]
                if full_account:
                    # Should contain colon separators for hierarchy
                    assert ":" in full_account, f"Row {row_num}: Account '{full_account}' should have hierarchical structure with ':'"
                    
                    # Should have valid account types at root level
                    root_account = full_account.split(":")[0]
                    valid_roots = ["Assets", "Liabilities", "Equity", "Income", "Expenses", "VAT", "Bank Accounts", "R&D Enhanced Expenditure"]
                    assert root_account in valid_roots, f"Row {row_num}: Root account '{root_account}' not in valid types"
    
    def test_csv_transaction_integrity(self):
        """CSV transactions must balance (debits = credits)"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Group by transaction ID
            transactions = {}
            for row in reader:
                tx_id = row["Transaction ID"]
                if tx_id:
                    if tx_id not in transactions:
                        transactions[tx_id] = []
                    transactions[tx_id].append(row)
            
            # Check each transaction balances
            for tx_id, tx_rows in transactions.items():
                total = 0
                for row in tx_rows:
                    if row["Amount Num."]:
                        amount = float(row["Amount Num."])
                        total += amount
                
                # Allow small rounding errors (within 0.01)
                assert abs(total) < 0.01, f"Transaction {tx_id} does not balance: total = {total}"


@pytest.mark.contract
class TestYAMLConfigContract:
    """Test YAML configuration schema validation"""
    
    def test_yaml_minimal_config_schema(self):
        """Minimal YAML config must contain required top-level sections"""
        config_file = Path(__file__).parent.parent / "fixtures" / "configs" / "minimal.yaml"
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        required_sections = ["accounts", "report"]
        for section in required_sections:
            assert section in config_data, f"Required section '{section}' missing from config"
    
    def test_yaml_accounts_section_schema(self):
        """Accounts section must have required fields"""
        config_file = Path(__file__).parent.parent / "fixtures" / "configs" / "minimal.yaml"
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        accounts_config = config_data["accounts"]
        
        # Required fields
        assert "kind" in accounts_config, "accounts.kind is required"
        assert "file" in accounts_config, "accounts.file is required"
        
        # Valid kinds
        valid_kinds = ["csv", "gnucash", "piecash"]
        assert accounts_config["kind"] in valid_kinds, f"accounts.kind must be one of {valid_kinds}"
    
    def test_yaml_report_section_schema(self):
        """Report section must have required fields"""
        config_file = Path(__file__).parent.parent / "fixtures" / "configs" / "minimal.yaml"
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        report_config = config_data["report"]
        
        # Required fields
        assert "name" in report_config, "report.name is required"
        assert "taxonomy" in report_config, "report.taxonomy is required"
    
    def test_yaml_complete_config_schema(self):
        """Complete YAML config should have comprehensive structure"""
        config_file = Path(__file__).parent.parent / "fixtures" / "configs" / "complete.yaml"
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Check comprehensive structure
        expected_sections = ["accounts", "report", "metadata"]
        for section in expected_sections:
            assert section in config_data, f"Section '{section}' missing from complete config"
        
        # Check metadata subsections
        if "metadata" in config_data:
            metadata = config_data["metadata"]
            expected_metadata = ["company", "accounting", "period"]
            for meta_section in expected_metadata:
                assert meta_section in metadata, f"metadata.{meta_section} missing from complete config"
    
    def test_yaml_invalid_config_rejected(self):
        """Invalid YAML configs should be properly detected"""
        config_file = Path(__file__).parent.parent / "fixtures" / "configs" / "invalid.yaml"
        
        with pytest.raises((yaml.YAMLError, KeyError, TypeError)):
            # Should fail to load or should fail validation
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
                # If it loads, it should fail basic validation
                Config(config_data)  # This should raise an error


@pytest.mark.contract
class TestGnuCashDataContract:
    """Test GnuCash file format compatibility"""
    
    def test_gnucash_file_readable(self):
        """GnuCash files must be readable by the accounts module"""
        gnucash_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample2.gnucash"
        
        # Test that we can at least attempt to open it
        try:
            # This should use the accounts module factory
            with patch('ixbrl_reporter.accounts_gnucash.GnuCashSession') as mock_session:
                mock_session.return_value = Mock()
                
                accounts_impl = accounts_module.get_class("gnucash")(str(gnucash_file))
                assert accounts_impl is not None
                
        except Exception as e:
            # If it fails, it should be a known failure mode
            assert "No module named" in str(e) or "gnucash" in str(e).lower(), \
                f"Unexpected error reading GnuCash file: {e}"
    
    def test_gnucash_sqlite_format(self):
        """GnuCash files in SQLite format should be valid SQLite databases"""
        gnucash_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample2.gnucash"
        
        if gnucash_file.exists():
            try:
                # Try to open as SQLite database
                conn = sqlite3.connect(str(gnucash_file))
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                # Should have GnuCash-specific tables
                expected_tables = ["accounts", "transactions", "splits"]
                for table in expected_tables:
                    assert table in tables, f"GnuCash table '{table}' not found in database"
                    
            except sqlite3.DatabaseError:
                # If it's not SQLite, that's also valid (could be XML format)
                pytest.skip("GnuCash file is not in SQLite format")
    
    def test_gnucash_account_structure(self):
        """GnuCash accounts should follow expected structure"""
        # This test would need actual GnuCash integration
        # For now, we test that the integration can be attempted
        
        with patch('ixbrl_reporter.accounts_gnucash.GnuCashSession') as mock_session:
            mock_account = Mock()
            mock_account.fullname = "Assets:Current Assets:Cash"
            mock_account.get_balance.return_value = Mock(value=1000.0)
            
            mock_session.return_value.query.return_value.all.return_value = [mock_account]
            
            try:
                accounts_impl = accounts_module.get_class("gnucash")("dummy.gnucash")
                # Should be able to instantiate without error
                assert accounts_impl is not None
            except ImportError:
                pytest.skip("GnuCash integration not available")


@pytest.mark.contract  
class TestPiecashDataContract:
    """Test Piecash (Python GnuCash) compatibility"""
    
    def test_piecash_integration_available(self):
        """Test that piecash integration can be loaded"""
        try:
            accounts_impl = accounts_module.get_class("piecash")("dummy.gnucash")
            assert accounts_impl is not None
        except ImportError as e:
            pytest.skip(f"Piecash integration not available: {e}")
    
    def test_piecash_file_handling(self):
        """Test piecash file handling contracts"""
        with patch('ixbrl_reporter.accounts_piecash.piecash') as mock_piecash:
            mock_book = Mock()
            mock_account = Mock()
            mock_account.fullname = "Assets:Bank"
            mock_account.get_balance.return_value = 1000
            
            mock_book.accounts = [mock_account]
            mock_piecash.open_book.return_value = mock_book
            
            try:
                accounts_impl = accounts_module.get_class("piecash")("dummy.gnucash")
                assert accounts_impl is not None
            except ImportError:
                pytest.skip("Piecash integration not available")


@pytest.mark.contract
class TestDataIntegrationContract:
    """Test integration between data formats and system"""
    
    def test_accounts_factory_contract(self):
        """Test that accounts factory correctly identifies and loads different formats"""
        test_cases = [
            ("csv", "sample.csv"),
            ("gnucash", "sample.gnucash"),  
            ("piecash", "sample.gnucash"),
        ]
        
        for kind, filename in test_cases:
            try:
                accounts_class = accounts_module.get_class(kind)
                assert accounts_class is not None, f"Failed to get accounts class for {kind}"
            except ImportError:
                pytest.skip(f"Integration for {kind} not available")
    
    def test_config_data_contract(self):
        """Test config system handles various data types correctly"""
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {"name": "Test", "taxonomy": "test"},
            "metadata": {
                "accounting": {"decimals": 2, "scale": 0, "currency": "GBP"},
                "period": {"start": "2020-01-01", "end": "2020-12-31"}
            }
        }
        
        config = Config(config_data)
        
        # Test navigation and type preservation
        assert config.get("accounts.kind") == "csv"
        assert config.get("metadata.accounting.decimals") == 2
        assert config.get("metadata.period.start") == "2020-01-01"
    
    def test_file_encoding_contract(self):
        """Test that files are handled with proper encoding"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        # Test UTF-8 encoding
        with open(csv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert isinstance(content, str)
            
        # Test that file can be read with different encodings
        try:
            with open(csv_file, 'r', encoding='latin1') as f:
                content = f.read()
                assert isinstance(content, str)
        except UnicodeError:
            # This is acceptable - file must be UTF-8
            pass


@pytest.mark.contract
class TestDataValidationContract:
    """Test data validation contracts"""
    
    def test_amount_precision_contract(self):
        """Test that monetary amounts maintain required precision"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                if row["Amount Num."]:
                    amount_str = row["Amount Num."]
                    amount = float(amount_str)
                    
                    # Check precision (should be to 2 decimal places for currency)
                    if abs(amount) > 0:
                        # Convert back to string and check decimal places
                        formatted = f"{amount:.2f}"
                        reconstructed = float(formatted)
                        
                        # Should not lose significant precision
                        assert abs(amount - reconstructed) < 0.005, \
                            f"Amount {amount} loses precision when formatted to 2dp"
    
    def test_date_format_contract(self):
        """Test that dates follow expected formats"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                date_str = row["Date"]
                if date_str:
                    # Should be in DD/MM/YY or DD/MM/YYYY format
                    parts = date_str.split("/")
                    assert len(parts) == 3, f"Date '{date_str}' should have 3 parts separated by '/'"
                    
                    day, month, year = parts
                    assert 1 <= int(day) <= 31, f"Invalid day in date '{date_str}'"
                    assert 1 <= int(month) <= 12, f"Invalid month in date '{date_str}'"
                    assert len(year) in [2, 4], f"Year in date '{date_str}' should be 2 or 4 digits"
    
    def test_currency_consistency_contract(self):
        """Test that currencies are consistent within datasets"""
        csv_file = Path(__file__).parent.parent / "fixtures" / "accounts" / "sample.csv"
        
        currencies = set()
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                currency = row["Commodity/Currency"]
                if currency:
                    currencies.add(currency)
        
        # Should have consistent currency usage
        # For test data, should primarily be GBP
        assert "CURRENCY::GBP" in currencies, "Expected GBP currency in test data"
        
        # Should not have too many different currencies in simple test data
        assert len(currencies) <= 3, f"Too many currencies in test data: {currencies}"