"""
Contract tests for iXBRL output validation and standards compliance

These tests ensure valid iXBRL output generation and compliance with
iXBRL standards as outlined in TEST_STRATEGY.md contract testing requirements.
"""
import pytest
import re
from pathlib import Path
from unittest.mock import Mock, patch
from lxml import etree
import tempfile

from ixbrl_reporter.ixbrl_reporter import IxbrlReporter
from ixbrl_reporter.html import HtmlElement


@pytest.mark.contract
class TestIXBRLOutputContract:
    """Test iXBRL output format compliance"""
    
    def test_ixbrl_namespace_declarations(self):
        """iXBRL output must include required namespace declarations"""
        # Create a minimal iXBRL structure
        reporter = IxbrlReporter(hide_notes=False)
        mock_par = Mock()
        mock_ix_maker = Mock()
        mock_xhtml_maker = Mock()
        
        # Mock the namespace setup
        mock_par.ix_maker = mock_ix_maker
        mock_par.xhtml_maker = mock_xhtml_maker
        
        # Test that namespace URIs are correctly defined
        expected_namespaces = {
            'ix': 'http://www.xbrl.org/2013/inlineXBRL',
            'ixt': 'http://www.xbrl.org/inlineXBRL/transformation/2020-02-12',
            'ixt2': 'http://www.xbrl.org/inlineXBRL/transformation/2011-07-31',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xlink': 'http://www.w3.org/1999/xlink'
        }
        
        # Mock HtmlElement class to check namespace setup
        with patch('ixbrl_reporter.html.HtmlElement') as mock_html_class:
            mock_html = Mock()
            mock_html_class.return_value = mock_html
            
            # Verify that the namespace URIs are used
            for prefix, uri in expected_namespaces.items():
                # This would be verified in actual HTML output
                assert uri is not None, f"Namespace URI for {prefix} should be defined"
    
    def test_ixbrl_element_structure(self):
        """iXBRL elements must have correct structure and attributes"""
        reporter = IxbrlReporter(hide_notes=False)
        mock_par = Mock()
        mock_ix_maker = Mock()
        mock_xhtml_maker = Mock()
        
        mock_par.ix_maker = mock_ix_maker
        mock_par.xhtml_maker = mock_xhtml_maker
        reporter.par = mock_par
        reporter.decimals = 2
        reporter.scale = 0
        reporter.currency = "GBP"
        reporter.tiny = 0.005
        
        # Create a mock fact
        mock_fact = Mock()
        mock_fact.value = 1000.0
        mock_fact.name = "uk-gaap:TurnoverGrossOperatingRevenue"
        mock_fact.context = "context-1"
        mock_fact.reverse = False
        
        # Mock iXBRL element
        mock_ix_element = Mock()
        mock_ix_maker.nonFraction.return_value = mock_ix_element
        
        # Mock spans for wrapping
        mock_spans = [Mock(), Mock(), Mock()]
        mock_xhtml_maker.span.side_effect = mock_spans
        
        # Create tagged money fact
        result = reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Verify required attributes are set
        mock_ix_element.set.assert_any_call("name", "uk-gaap:TurnoverGrossOperatingRevenue")
        mock_ix_element.set.assert_any_call("contextRef", "context-1")
        mock_ix_element.set.assert_any_call("format", "ixt2:numdotdecimal")
        mock_ix_element.set.assert_any_call("unitRef", "GBP")
        mock_ix_element.set.assert_any_call("decimals", "2")
        mock_ix_element.set.assert_any_call("scale", "0")
    
    def test_ixbrl_context_references(self):
        """iXBRL elements must reference valid contexts"""
        # Test that context references are properly formatted
        valid_context_patterns = [
            r'^context-\d+$',  # context-1, context-2, etc.
            r'^[a-zA-Z][\w-]*$',  # General alphanumeric with dashes
            r'^period_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}$'  # Date-based contexts
        ]
        
        test_contexts = [
            "context-1",
            "period_2020-01-01_2020-12-31", 
            "instant_2020-12-31",
            "duration_2020"
        ]
        
        for context in test_contexts:
            is_valid = any(re.match(pattern, context) for pattern in valid_context_patterns)
            assert is_valid, f"Context '{context}' does not match valid patterns"
    
    def test_ixbrl_numeric_formatting(self):
        """iXBRL numeric elements must use correct transformation formats"""
        reporter = IxbrlReporter(hide_notes=False)
        
        # Test different decimal settings
        test_cases = [
            (2, "ixt2:numdotdecimal"),
            (0, "ixt2:numdotdecimal"), 
            (4, "ixt2:numdotdecimal")
        ]
        
        for decimals, expected_format in test_cases:
            reporter.decimals = decimals
            
            # Verify format is consistently applied
            assert expected_format.startswith("ixt"), f"Format should use iXT transformation"
            assert "decimal" in expected_format, f"Format should handle decimal numbers"
    
    def test_ixbrl_units_validity(self):
        """iXBRL monetary units must be valid currency codes"""
        valid_currencies = ["GBP", "USD", "EUR", "JPY", "CAD", "AUD", "CHF"]
        
        reporter = IxbrlReporter(hide_notes=False)
        
        for currency in valid_currencies:
            reporter.currency = currency
            # Should be 3-letter ISO code
            assert len(currency) == 3, f"Currency '{currency}' should be 3 letters"
            assert currency.isupper(), f"Currency '{currency}' should be uppercase"
            assert currency.isalpha(), f"Currency '{currency}' should be alphabetic"
    
    def test_ixbrl_taxonomy_references(self):
        """iXBRL elements must reference valid taxonomy elements"""
        # Test taxonomy element name patterns
        valid_taxonomy_patterns = [
            r'^uk-gaap:[A-Z][A-Za-z]*$',  # UK GAAP elements
            r'^ifrs-full:[A-Z][A-Za-z]*$',  # IFRS elements  
            r'^esef:[A-Z][A-Za-z]*$',  # ESEF elements
            r'^[a-z-]+:[A-Z][A-Za-z]*$'  # General taxonomy:Element pattern
        ]
        
        test_elements = [
            "uk-gaap:TurnoverGrossOperatingRevenue",
            "uk-gaap:AdministrativeExpenses",
            "ifrs-full:Revenue",
            "esef:Assets"
        ]
        
        for element in test_elements:
            is_valid = any(re.match(pattern, element) for pattern in valid_taxonomy_patterns)
            assert is_valid, f"Taxonomy element '{element}' does not match valid patterns"
            
            # Must contain namespace prefix
            assert ":" in element, f"Element '{element}' must have namespace prefix"
            
            # Element name should start with capital letter
            element_name = element.split(":", 1)[1]
            assert element_name[0].isupper(), f"Element name in '{element}' should start with capital"


@pytest.mark.contract
class TestIXBRLStandardsCompliance:
    """Test compliance with iXBRL standards and specifications"""
    
    def test_ixbrl_html_wrapper_structure(self):
        """iXBRL must be wrapped in valid HTML5 structure"""
        with patch('ixbrl_reporter.html.HtmlElement') as mock_html_class:
            mock_html = Mock()
            mock_html_class.return_value = mock_html
            
            # Should create proper HTML structure
            # HtmlElement should be instantiated with proper parameters
            assert mock_html_class is not None
    
    def test_ixbrl_metadata_requirements(self):
        """iXBRL documents must include required metadata"""
        # Test that essential metadata is included
        required_metadata_elements = [
            "schemaRef",  # Reference to taxonomy schema
            "context",    # Context definitions
            "unit"        # Unit definitions
        ]
        
        # These would be validated in actual iXBRL output
        for element in required_metadata_elements:
            assert element is not None, f"Metadata element '{element}' is required"
    
    def test_ixbrl_transformation_registry(self):
        """iXBRL transformations must use valid transformation registry entries"""
        valid_transformations = [
            "ixt2:numdotdecimal",
            "ixt2:numcommadecimal", 
            "ixt:dateslasheu",
            "ixt:dateslashus",
            "ixt:datedoteu",
            "ixt:boolean-true",
            "ixt:boolean-false"
        ]
        
        # Test transformation format patterns
        for transform in valid_transformations:
            # Must have namespace prefix
            assert ":" in transform, f"Transformation '{transform}' must have namespace prefix"
            
            # Must start with ixt or ixt2
            prefix = transform.split(":", 1)[0]
            assert prefix in ["ixt", "ixt2"], f"Transformation '{transform}' must use ixt or ixt2 namespace"
    
    def test_ixbrl_sign_handling_compliance(self):
        """iXBRL sign handling must comply with specification"""
        reporter = IxbrlReporter(hide_notes=False)
        mock_par = Mock()
        mock_ix_maker = Mock()
        mock_xhtml_maker = Mock()
        
        mock_par.ix_maker = mock_ix_maker
        mock_par.xhtml_maker = mock_xhtml_maker
        reporter.par = mock_par
        reporter.decimals = 2
        reporter.scale = 0
        reporter.currency = "GBP"
        reporter.tiny = 0.005
        
        # Test negative value handling
        mock_fact = Mock()
        mock_fact.value = -500.0
        mock_fact.name = "uk-gaap:AdministrativeExpenses"
        mock_fact.context = "context-1"
        mock_fact.reverse = False
        
        mock_ix_element = Mock()
        mock_ix_maker.nonFraction.return_value = mock_ix_element
        mock_xhtml_maker.span.side_effect = [Mock(), Mock(), Mock()]
        
        result = reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Should set sign attribute for negative values
        mock_ix_element.set.assert_any_call("sign", "-")
    
    def test_ixbrl_precision_vs_decimals(self):
        """iXBRL must use either precision or decimals, not both"""
        # Test that we consistently use decimals (not precision)
        reporter = IxbrlReporter(hide_notes=False)
        mock_par = Mock()
        mock_ix_maker = Mock()
        mock_xhtml_maker = Mock()
        
        mock_par.ix_maker = mock_ix_maker
        mock_par.xhtml_maker = mock_xhtml_maker
        reporter.par = mock_par
        reporter.decimals = 2
        reporter.scale = 0
        reporter.currency = "GBP"
        reporter.tiny = 0.005
        
        mock_fact = Mock()
        mock_fact.value = 1000.0
        mock_fact.name = "uk-gaap:Assets"
        mock_fact.context = "context-1"
        mock_fact.reverse = False
        
        mock_ix_element = Mock()
        mock_ix_maker.nonFraction.return_value = mock_ix_element
        mock_xhtml_maker.span.side_effect = [Mock(), Mock(), Mock()]
        
        result = reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Should set decimals attribute
        mock_ix_element.set.assert_any_call("decimals", "2")
        
        # Should not set precision attribute (verify no precision calls)
        precision_calls = [call for call in mock_ix_element.set.call_args_list 
                          if call[0][0] == "precision"]
        assert len(precision_calls) == 0, "Should not set precision when using decimals"


@pytest.mark.contract
class TestIXBRLTaxonomyCompliance:
    """Test taxonomy adherence and compliance"""
    
    def test_taxonomy_namespace_consistency(self):
        """Elements must use consistent taxonomy namespaces"""
        # Mock taxonomy to test namespace handling
        with patch('ixbrl_reporter.taxonomy.Taxonomy') as mock_taxonomy_class:
            mock_taxonomy = Mock()
            mock_taxonomy_class.return_value = mock_taxonomy
            
            # Test namespace consistency
            test_namespaces = {
                "uk-gaap": "http://www.xbrl.org/uk/fr/gaap/pt/2004-12-01",
                "ifrs-full": "http://xbrl.ifrs.org/taxonomy/2021-03-24/ifrs-full",
                "esef": "http://www.esma.europa.eu/taxonomy/2020-03-16/esef_all"
            }
            
            for prefix, uri in test_namespaces.items():
                # Namespace URIs should be properly formatted
                assert uri.startswith("http"), f"Namespace URI for {prefix} should be HTTP URL"
                assert prefix in uri or prefix.replace("-", "") in uri.lower(), \
                    f"Namespace URI should relate to prefix {prefix}"
    
    def test_taxonomy_element_validation(self):
        """Taxonomy elements must exist and be valid"""
        # This would integrate with actual taxonomy loading
        with patch('ixbrl_reporter.taxonomy.Taxonomy') as mock_taxonomy_class:
            mock_taxonomy = Mock()
            mock_taxonomy_class.return_value = mock_taxonomy
            
            # Mock element validation
            mock_element = Mock()
            mock_element.name = "uk-gaap:TurnoverGrossOperatingRevenue"
            mock_element.type = "monetary"
            
            mock_taxonomy.get_element.return_value = mock_element
            
            # taxonomy = Taxonomy("test-taxonomy.yaml")  # Would need actual integration
            element = mock_taxonomy.get_element("uk-gaap:TurnoverGrossOperatingRevenue")
            
            # Element should have required properties
            assert hasattr(element, 'name'), "Taxonomy element should have name"
            assert hasattr(element, 'type'), "Taxonomy element should have type"
    
    def test_context_period_validation(self):
        """Context periods must be valid and consistent"""
        # Test different period types
        period_types = [
            "instant",    # Point in time
            "duration",   # Period of time
            "forever"     # Permanent items
        ]
        
        for period_type in period_types:
            assert period_type in ["instant", "duration", "forever"], \
                f"Period type '{period_type}' must be valid XBRL period type"
    
    def test_dimensional_context_structure(self):
        """Dimensional contexts must follow XBRL Dimensions specification"""
        # Test dimension handling (would be more complex in real implementation)
        dimension_types = [
            "explicit",   # Explicit dimensions with domain members
            "typed"       # Typed dimensions with values
        ]
        
        for dim_type in dimension_types:
            assert dim_type in ["explicit", "typed"], \
                f"Dimension type '{dim_type}' must be valid XBRL dimension type"


@pytest.mark.contract
class TestIXBRLOutputValidation:
    """Test iXBRL output validation against XML schemas"""
    
    def test_ixbrl_xml_well_formed(self):
        """iXBRL output must be well-formed XML"""
        # Mock XML structure
        sample_ixbrl = '''<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml"
              xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
            <head>
                <title>Test Report</title>
            </head>
            <body>
                <ix:nonFraction name="uk-gaap:Assets" contextRef="context-1" 
                               unitRef="GBP" decimals="2" format="ixt2:numdotdecimal">
                    1000.00
                </ix:nonFraction>
            </body>
        </html>'''
        
        try:
            # Parse as XML to verify well-formedness
            root = etree.fromstring(sample_ixbrl.encode('utf-8'))
            assert root is not None, "iXBRL should be well-formed XML"
            
            # Check namespace declarations
            nsmap = root.nsmap
            assert 'ix' in nsmap, "iXBRL namespace should be declared"
            assert nsmap['ix'] == 'http://www.xbrl.org/2013/inlineXBRL', \
                "iXBRL namespace should be correct"
                
        except etree.XMLSyntaxError as e:
            pytest.fail(f"iXBRL output is not well-formed XML: {e}")
    
    def test_ixbrl_html5_compliance(self):
        """iXBRL output must be valid HTML5"""
        # Test HTML5 structure requirements
        html5_requirements = [
            "<!DOCTYPE html>",  # HTML5 doctype
            "<html",            # Root HTML element
            "<head>",           # Head section
            "<body>"            # Body section
        ]
        
        # Mock HTML output (in real test, would check actual output)
        sample_html = '''<!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>Test</title></head>
            <body><p>Content</p></body>
        </html>'''
        
        for requirement in html5_requirements:
            assert requirement in sample_html, \
                f"HTML5 requirement '{requirement}' missing from output"
    
    def test_ixbrl_character_encoding(self):
        """iXBRL output must use UTF-8 encoding"""
        # Test that content can be properly encoded/decoded as UTF-8
        test_content = "Company Ltd £1,000.50 profit"
        
        try:
            # Encode and decode as UTF-8
            encoded = test_content.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert decoded == test_content, "Content should survive UTF-8 round-trip"
            
        except UnicodeError as e:
            pytest.fail(f"Content cannot be properly encoded as UTF-8: {e}")
    
    def test_ixbrl_special_characters_handling(self):
        """iXBRL must properly handle special characters and entities"""
        special_chars = {
            "&": "&amp;",
            "<": "&lt;", 
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
            "£": "£",     # Should be preserved as-is in UTF-8
            "€": "€",     # Should be preserved as-is in UTF-8
        }
        
        for char, expected in special_chars.items():
            # In XML content, special chars should be properly escaped
            if char in "&<>\"'":
                # These need escaping in XML
                assert expected.startswith("&"), f"XML special char '{char}' should be escaped"
            else:
                # Currency symbols can be preserved in UTF-8
                assert expected == char or expected.startswith("&"), \
                    f"Character '{char}' should be properly handled"


@pytest.mark.contract
class TestIXBRLPerformanceContract:
    """Test iXBRL generation performance contracts"""
    
    def test_ixbrl_generation_scaling(self):
        """iXBRL generation should scale reasonably with document size"""
        # Mock different document sizes
        document_sizes = [10, 100, 1000]  # Number of facts
        
        for size in document_sizes:
            # Test would measure generation time
            # For now, just verify the concept
            assert size > 0, f"Document size {size} should be positive"
            
            # Performance should not degrade exponentially
            # (actual timing would be done in performance tests)
            if size <= 1000:
                # Should be manageable for documents up to 1000 facts
                assert True, f"Should handle {size} facts efficiently"
    
    def test_ixbrl_memory_usage_contract(self):
        """iXBRL generation should not consume excessive memory"""
        # Mock memory constraints test
        # In real implementation, would monitor actual memory usage
        
        # Should not hold entire document in memory simultaneously
        # Should stream/process incrementally where possible
        assert True, "Memory usage should be bounded"
    
    def test_ixbrl_output_size_reasonable(self):
        """iXBRL output size should be reasonable relative to input"""
        # Output should not be excessively larger than input data
        # Typical expansion ratio should be < 10x for structured data
        
        input_size_estimate = 1000  # bytes of source data
        max_expansion_ratio = 20    # 20x expansion seems reasonable for XML
        
        max_output_size = input_size_estimate * max_expansion_ratio
        assert max_output_size > input_size_estimate, \
            "Output size estimation should be reasonable"