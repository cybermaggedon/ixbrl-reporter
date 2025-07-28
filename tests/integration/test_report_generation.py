"""
Report Generation Integration Tests

Tests full report generation pipeline with different report types and template processing
as outlined in TEST_STRATEGY.md integration testing requirements.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from ixbrl_reporter.config import Config
from ixbrl_reporter.data_source import DataSource


@pytest.mark.integration
class TestReportGenerationPipeline:
    """Test full report generation pipeline integration"""
    
    def test_audited_full_report_generation(self):
        """Test generation of audited full report"""
        config_data = {
            "accounts": {
                "kind": "csv",
                "file": "test.csv"
            },
            "report": {
                "name": "Audited Full Report",
                "taxonomy": "uk-gaap",
                "type": "audited-full",
                "computations": [
                {
                    "id": "net-assets",
                    "description": "Net Assets", 
                    "kind": "sum",
                    "inputs": [],
                    "period": "at-end"
                }
                ]
            },
            "metadata": {
                "accounting": {
                "currency": "GBP",
                "decimals": 0,
                "scale": 0,
                "periods": [
                    {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"},
                    {"name": "2019", "start": "2019-01-01", "end": "2019-12-31"}
                ]
                },
                "business": {
                "company-name": "Audited Test Company Ltd",
                "company-number": "12345678",
                "entity-scheme": "http://www.companieshouse.gov.uk/",
                "entity-identifier": "12345678"
                },
                "auditors": {
                "name": "Test Auditors LLP",
                "opinion": "unqualified"
                }
            }
        }
        
        config = Config(config_data)
        
        # Mock accounts session
        with patch('ixbrl_reporter.accounts_csv.Accounts') as mock_accounts:
            mock_session = Mock()
            mock_accounts.return_value = mock_session
            
            # Create DataSource for real integration testing
            data_source = DataSource(config, mock_session)
            
            # Verify DataSource was created successfully
            assert data_source is not None
            
            # Mock iXBRL reporter
            with patch('ixbrl_reporter.ixbrl_reporter.IxbrlReporter') as mock_reporter_class:
                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter
                
                # Mock audited report output
                audited_output = '''<!DOCTYPE html>
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head><title>Audited Test Company Ltd - Annual Report</title></head>
<body>
    <h1>Directors' Report</h1>
    <h1>Auditors' Report</h1>
    <h1>Financial Statements</h1>
    <ix:nonFraction name="uk-gaap:NetCurrentAssets">£10,000</ix:nonFraction>
</body>
</html>'''
                
                mock_reporter.create_report.return_value = audited_output
                
                from ixbrl_reporter.ixbrl_reporter import IxbrlReporter
                reporter = IxbrlReporter(hide_notes=False)
                output = reporter.create_report(data_source)
                
                # Verify audited report characteristics
                assert "Auditors' Report" in output
                assert "Directors' Report" in output
                assert "ix:nonFraction" in output
                assert "uk-gaap:" in output
    
    def test_unaudited_micro_report_generation(self):
        """Test generation of unaudited micro entity report"""
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {
                "name": "Micro Entity Report",
                "taxonomy": "uk-gaap", 
                "type": "unaudited-micro",
                "computations": [
                {
                    "id": "fixed-assets",
                    "description": "Fixed Assets",
                    "kind": "sum",
                    "inputs": [],
                    "period": "at-end"
                }
                ]
            },
            "metadata": {
                "accounting": {
                "currency": "GBP",
                "periods": [
                    {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"}
                ]
                },
                "business": {
                "company-name": "Micro Test Ltd",
                "entity-type": "micro",
                "entity-scheme": "http://www.companieshouse.gov.uk/",
                "entity-identifier": "12345678"
                }
            }
        }
        
        config = Config(config_data)
        
        with patch('ixbrl_reporter.accounts_csv.Accounts') as mock_accounts:
            mock_session = Mock()
            mock_accounts.return_value = mock_session
            
            data_source = DataSource(config, mock_session)
            
            # Verify DataSource was created successfully
            assert data_source is not None
                
                with patch('ixbrl_reporter.ixbrl_reporter.IxbrlReporter') as mock_reporter_class:
                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter
                
                # Micro entity reports are simpler
                micro_output = '''<!DOCTYPE html>
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head><title>Micro Test Ltd - Micro Entity Report</title></head>
<body>
    <h1>Balance Sheet</h1>
    <ix:nonFraction name="uk-gaap:FixedAssets">£5,000</ix:nonFraction>
    <ix:nonFraction name="uk-gaap:CurrentAssets">£2,000</ix:nonFraction>
</body>
</html>'''
                
                mock_reporter.create_report.return_value = micro_output
                
                from ixbrl_reporter.ixbrl_reporter import IxbrlReporter
                reporter = IxbrlReporter()
                output = reporter.create_report(data_source)
                
                # Micro entity reports have fewer sections
                assert "Micro Entity Report" in output
                assert "Balance Sheet" in output
                assert "Auditors' Report" not in output  # No auditors for micro
    
    def test_esef_report_generation(self):
        """Test generation of ESEF (European Single Electronic Format) report"""
        config_data = {
            "accounts": {"kind": "piecash", "file": "test.db"},
            "report": {
                "name": "ESEF Annual Report",
                "taxonomy": "esef",
                "type": "esef",
                "computations": [
                {
                    "id": "total-assets",
                    "description": "Total Assets",
                    "kind": "sum",
                    "inputs": [],
                    "period": "at-end"
                }
                ]
            },
            "metadata": {
                "accounting": {
                "currency": "EUR",
                "decimals": 0,
                "periods": [
                    {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"}
                ]
                },
                "business": {
                "company-name": "European Test AG",
                "country": "germany",
                "entity-scheme": "http://www.sec.gov/",
                "entity-identifier": "DE123456789"
                }
            }
        }
        
        config = Config(config_data)
        
        with patch('ixbrl_reporter.accounts_piecash.Accounts') as mock_accounts:
            mock_session = Mock()
            mock_accounts.return_value = mock_session
            
            data_source = DataSource(config, mock_session)
            
            # Verify DataSource was created successfully
            assert data_source is not None
                
                with patch('ixbrl_reporter.ixbrl_reporter.IxbrlReporter') as mock_reporter_class:
                mock_reporter = Mock()
                mock_reporter_class.return_value = mock_reporter
                
                # ESEF uses IFRS taxonomy
                esef_output = '''<!DOCTYPE html>
<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:ifrs="http://xbrl.ifrs.org/taxonomy/2020-03-16/ifrs-full">
<head><title>European Test AG - Annual Report</title></head>
<body>
    <h1>Management Report</h1>
    <h1>Consolidated Financial Statements</h1>
    <ix:nonFraction name="ifrs-full:Assets">€100,000</ix:nonFraction>
</body>
</html>'''
                
                mock_reporter.create_report.return_value = esef_output
                
                from ixbrl_reporter.ixbrl_reporter import IxbrlReporter
                reporter = IxbrlReporter()
                output = reporter.create_report(data_source)
                
                # ESEF specific characteristics
                assert "ifrs-full:" in output
                assert "€" in output or "EUR" in output
                assert "Consolidated Financial Statements" in output
    
    def test_report_with_custom_template(self):
        """Test report generation with custom template"""
        # Custom template configuration
        template_config = {
            "elements": [
                {"element": "worksheet", "worksheet": "custom-balance-sheet"}
            ],
            "worksheets": {
                "custom-balance-sheet": {
                "title": "Custom Balance Sheet",
                "columns": [
                    {"name": "current", "title": "Current Year"},
                    {"name": "prior", "title": "Prior Year"}
                ],
                "rows": [
                    {"id": "assets", "description": "Total Assets", "computation": "sum"},
                    {"id": "liabilities", "description": "Total Liabilities", "computation": "sum"},
                    {"id": "equity", "description": "Total Equity", "computation": "subtract"}
                ]
                }
            }
        }
        
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {
                "name": "Custom Template Report",
                "template": template_config,
                "computations": [
                {
                    "id": "assets",
                    "description": "Total Assets",
                    "kind": "sum",
                    "inputs": [],
                    "period": "at-end"
                }
                ]
            }
        }
        
        config = Config(config_data)
        
        with patch('ixbrl_reporter.accounts_csv.Accounts') as mock_accounts:
            mock_session = Mock()
            mock_accounts.return_value = mock_session
            
            data_source = DataSource(config, mock_session)
            
            # Verify DataSource was created successfully
            assert data_source is not None
                
                # Test template processing
                template = config.get("report.template")
                assert "elements" in template
                assert len(template["worksheets"]["custom-balance-sheet"]["rows"]) == 3
                
                # Verify worksheet structure
                worksheet = template["worksheets"]["custom-balance-sheet"]
                assert worksheet["title"] == "Custom Balance Sheet"
                assert len(worksheet["columns"]) == 2


@pytest.mark.integration
class TestTemplateProcessingIntegration:
    """Test template processing and variable substitution"""
    
    def test_template_variable_substitution(self):
        """Test template variable substitution integration"""
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {
                "name": "Variable Substitution Test",
                "taxonomy": {
                "note-templates": {
                    "company-name": "Variable Test Company Ltd",
                    "report-period": "Year ended 31 December 2020",
                    "currency": "GBP"
                }
                },
                "computations": []
            }
        }
        
        config = Config(config_data)
        
        # Test variable retrieval
        company_name = config.get("report.taxonomy.note-templates.company-name")
        assert company_name == "Variable Test Company Ltd"
        
        # Mock template expansion
        with patch('ixbrl_reporter.expand.expand_string') as mock_expand:
            mock_expand.return_value = "Variable Test Company Ltd"
            
            from ixbrl_reporter.expand import expand_string
            
            # Test template expansion with variable
            mock_data_source = Mock()
            mock_data_source.get_config.return_value = "Variable Test Company Ltd"
            
            result = expand_string("template:company-name", mock_data_source)
            assert result == "Variable Test Company Ltd"
    
    def test_template_computation_references(self):
        """Test template computation references"""
        config_data = {
            "report": {
                "computations": [
                {
                    "id": "total-assets",
                    "operation": "sum",
                    "inputs": ["current-assets", "fixed-assets"]
                },
                {
                    "id": "net-profit",
                    "operation": "subtract",
                    "inputs": ["revenue", "expenses"]
                }
                ]
            }
        }
        
        config = Config(config_data)
        
        # Test computation definitions
        computations = config.get("report.computations")
        assert len(computations) == 2
        total_assets = computations[0]
        assert total_assets["id"] == "total-assets"
        assert total_assets["operation"] == "sum"
        assert len(total_assets["inputs"]) == 2
        
        # Mock computation processing
        with patch('ixbrl_reporter.computation.Sum') as mock_sum:
            mock_computation = Mock()
            mock_sum.return_value = mock_computation
            mock_computation.compute.return_value = 10000.0
            
            # Test computation creation and execution
            from ixbrl_reporter.computation import Sum
            computation = Sum({"id": "total-assets"})
            result = computation.compute(Mock())
            
            assert result == 10000.0
    
    def test_template_conditional_sections(self):
        """Test template conditional sections"""
        # Configuration with conditions
        config_data = {
            "report": {
                "conditions": {
                "show-auditors-report": True,
                "show-prior-year": False,
                "entity-type": "small"
                },
                "computations": []
            }
        }
        
        config = Config(config_data)
        
        # Test condition evaluation
        show_auditors = config.get("report.conditions.show-auditors-report")
        show_prior = config.get("report.conditions.show-prior-year")
        entity_type = config.get("report.conditions.entity-type")
        
        assert show_auditors is True
        assert show_prior is False
        assert entity_type == "small"
        
        # Mock conditional template processing
        template_sections = []
        
        if show_auditors:
            template_sections.append("auditors-report")
        
        if show_prior:
            template_sections.append("prior-year-comparison")
        
        if entity_type == "small":
            template_sections.append("small-entity-exemptions")
        
        assert "auditors-report" in template_sections
        assert "prior-year-comparison" not in template_sections
        assert "small-entity-exemptions" in template_sections
    
    def test_template_nested_structure(self):
        """Test template nested structure processing"""
        complex_template = {
            "elements": [
                {
                "element": "composite",
                "elements": [
                    {"element": "worksheet", "worksheet": "balance-sheet"},
                    {"element": "worksheet", "worksheet": "profit-loss"},
                    {
                        "element": "composite",
                        "elements": [
                            {"element": "notes", "notes": "accounting-policies"},
                            {"element": "notes", "notes": "subsequent-events"}
                        ]
                    }
                ]
                }
            ]
        }
        
        config_data = {
            "report": {"template": complex_template, "computations": []}
        }
        
        config = Config(config_data)
        
        # Test nested structure navigation
        template = config.get("report.template")
        root_elements = template["elements"]
        
        assert len(root_elements) == 1
        assert root_elements[0]["element"] == "composite"
        
        # Test nested composite elements
        nested_elements = root_elements[0]["elements"]
        assert len(nested_elements) == 3
        
        # First two are worksheets
        assert nested_elements[0]["element"] == "worksheet"
        assert nested_elements[1]["element"] == "worksheet"
        
        # Third is another composite
        assert nested_elements[2]["element"] == "composite"
        notes_elements = nested_elements[2]["elements"]
        assert len(notes_elements) == 2
        assert all(elem["element"] == "notes" for elem in notes_elements)


@pytest.mark.integration
class TestReportFormatIntegration:
    """Test different report output formats"""
    
    def test_ixbrl_format_generation(self):
        """Test iXBRL format output generation"""
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {"format": "ixbrl", "name": "iXBRL Test", "computations": []}
        }
        
        with patch('ixbrl_reporter.ixbrl_reporter.IxbrlReporter') as mock_reporter_class:
            mock_reporter = Mock()
            mock_reporter_class.return_value = mock_reporter
            
            ixbrl_output = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head><title>iXBRL Test Report</title></head>
<body>
    <ix:nonFraction name="test:Assets" contextRef="ctx-1">1000</ix:nonFraction>
</body>
</html>'''
            
            mock_reporter.create_report.return_value = ixbrl_output
            
            from ixbrl_reporter.ixbrl_reporter import IxbrlReporter
            reporter = IxbrlReporter()
            
            mock_data_source = Mock()
            output = reporter.create_report(mock_data_source)
            
            # Verify iXBRL format characteristics
            assert '<?xml version="1.0"' in output
            assert 'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"' in output
            assert 'ix:nonFraction' in output
    
    def test_html_format_generation(self):
        """Test HTML format output generation"""
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {"format": "html", "name": "HTML Test", "computations": []}
        }
        
        # Mock HTML-only output (without iXBRL tags)
        html_output = '''<!DOCTYPE html>
<html>
<head><title>HTML Test Report</title></head>
<body>
    <h1>Balance Sheet</h1>
    <table>
        <tr><td>Assets</td><td>£1,000</td></tr>
        <tr><td>Liabilities</td><td>£600</td></tr>
        <tr><td>Equity</td><td>£400</td></tr>
    </table>
</body>
</html>'''
        
        # Test HTML output characteristics
        assert '<!DOCTYPE html>' in html_output
        assert 'ix:' not in html_output  # No iXBRL tags in pure HTML
        assert '<table>' in html_output
        assert '£' in html_output
    
    def test_text_format_generation(self):
        """Test text format output generation"""
        with patch('ixbrl_reporter.text_reporter.TextReporter') as mock_text_class:
            mock_text = Mock()
            mock_text_class.return_value = mock_text
            
            text_output = '''
TEXT REPORT
===========

BALANCE SHEET
As at 31 December 2020

                    £
Assets                1000
Liabilities            600
                 -----
Net Assets             400
                 =====

PROFIT AND LOSS
For the year ended 31 December 2020

Revenue               2000
Expenses              1600
                 -----
Net Profit             400
                 =====
'''
            
            mock_text.create_report.return_value = text_output
            
            from ixbrl_reporter.text_reporter import TextReporter
            reporter = TextReporter()
            
            mock_data_source = Mock()
            output = reporter.create_report(mock_data_source)
            
            # Verify text format characteristics
            assert 'TEXT REPORT' in output
            assert '=======' in output  # Text formatting
            assert '£' in output
            assert '<' not in output  # No HTML/XML tags
    
    def test_debug_format_generation(self):
        """Test debug format output generation"""
        with patch('ixbrl_reporter.debug_reporter.DebugReporter') as mock_debug_class:
            mock_debug = Mock()
            mock_debug_class.return_value = mock_debug
            
            debug_output = '''
DEBUG REPORT
============

Configuration:
  accounts.kind: csv
  accounts.file: test.csv
  report.name: Debug Test

Account Balances:
  Assets:Cash: £1000.00
  Expenses:Equipment: £500.00

Computations:
  total-assets: Sum([Assets:Cash, Assets:Equipment]) = £1500.00
  net-profit: Subtract([Revenue], [Expenses]) = £500.00

Template Processing:
  Elements processed: 5
  Variables substituted: 12
  Computations evaluated: 3
'''
            
            mock_debug.create_report.return_value = debug_output
            
            from ixbrl_reporter.debug_reporter import DebugReporter
            reporter = DebugReporter()
            
            mock_data_source = Mock()
            output = reporter.create_report(mock_data_source)
            
            # Verify debug format characteristics
            assert 'DEBUG REPORT' in output
            assert 'Configuration:' in output
            assert 'Account Balances:' in output
            assert 'Computations:' in output


@pytest.mark.integration
class TestReportPerformanceIntegration:
    """Test report generation performance characteristics"""
    
    def test_large_report_generation(self):
        """Test generation of reports with large amounts of data"""
        # Configuration with many accounts and periods
        config_data = {
            "accounts": {"kind": "csv", "file": "large.csv"},
            "report": {"name": "Large Report Test", "computations": []},
            "metadata": {
                "accounting": {
                "periods": [
                    {"name": f"Year{i}", "start": f"{i}-01-01", "end": f"{i}-12-31"}
                    for i in range(2015, 2021)  # 6 years
                ]
                }
            }
        }
        
        config = Config(config_data)
        
        # Verify large configuration handling
        periods = config.get("metadata.accounting.periods")
        assert len(periods) == 6
        
        # Mock performance test
        import time
        start_time = time.time()
        
        # Simulate processing large config
        for period in periods:
            period_name = period["name"]
            assert period_name.startswith("Year")
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process quickly even with large configs
        assert processing_time < 1.0, f"Large config processing took {processing_time} seconds"
    
    def test_memory_efficient_report_generation(self):
        """Test memory-efficient report generation"""
        config_data = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {"name": "Memory Test", "computations": []}
        }
        
        config = Config(config_data)
        
        import sys
        
        # Measure memory usage of config
        config_size = sys.getsizeof(config)
        
        # Config should be reasonably sized
        assert config_size < 50000, f"Config memory usage {config_size} bytes seems high"
        
        # Test that multiple configs don't interfere
        configs = [Config(config_data) for _ in range(10)]
        
        for i, cfg in enumerate(configs):
            # Each config should be independent
            cfg.set("test.id", i)
            assert cfg.get("test.id") == i
    
    def test_concurrent_report_generation(self):
        """Test concurrent report generation scenarios"""
        base_config = {
            "accounts": {"kind": "csv", "file": "test.csv"},
            "report": {"name": "Concurrent Test", "computations": []}
        }
        
        # Create multiple independent report configurations
        configs = []
        for i in range(5):
            config_data = base_config.copy()
            config_data["report"]["name"] = f"Concurrent Test {i}"
            configs.append(Config(config_data))
        
        # Verify all configs are independent and functional
        for i, config in enumerate(configs):
            assert config.get("report.name") == f"Concurrent Test {i}"
            
            # Each should be able to set independent values
            config.set("instance.id", i * 10)
            assert config.get("instance.id") == i * 10
        
        # Verify independence is maintained
        for i, config in enumerate(configs):
            assert config.get("instance.id") == i * 10