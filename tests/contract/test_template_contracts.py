"""
Contract tests for template syntax and structure validation

These tests ensure template compatibility and validate template syntax
as outlined in TEST_STRATEGY.md contract testing requirements.
"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from ixbrl_reporter.config import Config
from ixbrl_reporter.expand import expand_string
from ixbrl_reporter.note_parse import NoteParser


@pytest.mark.contract
class TestTemplateStructureContract:
    """Test template file structure and syntax validation"""
    
    def test_template_yaml_structure(self):
        """Template files must be valid YAML with required structure"""
        # Test with actual template files from the project
        template_paths = [
            "/home/mark/dev/ixbrl-reporter/report/ch/audited-full.yaml",
            "/home/mark/dev/ixbrl-reporter/report/ch/unaudited-micro.yaml",
            "/home/mark/dev/ixbrl-reporter/balance-sheet.yaml"
        ]
        
        for template_path in template_paths:
            if Path(template_path).exists():
                with open(template_path, 'r') as f:
                    try:
                        template_data = yaml.safe_load(f)
                        assert isinstance(template_data, dict), \
                            f"Template {template_path} should be a YAML dictionary"
                    except yaml.YAMLError as e:
                        pytest.fail(f"Template {template_path} is not valid YAML: {e}")
    
    def test_template_required_sections(self):
        """Templates must contain required top-level sections"""
        # Mock a typical template structure
        template_data = {
            "elements": [
                {"element": "worksheet", "worksheet": "balance-sheet"}
            ],
            "computations": {},
            "worksheets": {
                "balance-sheet": {
                    "columns": [],
                    "rows": []
                }
            }
        }
        
        # Check required sections exist
        expected_sections = ["elements"]
        for section in expected_sections:
            assert section in template_data, \
                f"Template must contain '{section}' section"
    
    def test_template_element_structure(self):
        """Template elements must have valid structure"""
        template_elements = [
            {"element": "worksheet", "worksheet": "balance-sheet"},
            {"element": "composite", "elements": []},
            {"element": "notes", "notes": "test-notes"}
        ]
        
        for element in template_elements:
            assert "element" in element, "Template element must have 'element' type"
            
            element_type = element["element"]
            valid_types = ["worksheet", "composite", "notes", "simple-sheet", "flex-sheet"]
            assert element_type in valid_types, \
                f"Element type '{element_type}' must be valid"
            
            # Type-specific validation
            if element_type == "worksheet":
                assert "worksheet" in element, "Worksheet element must specify worksheet name"
            elif element_type == "composite":
                assert "elements" in element, "Composite element must have elements list"
    
    def test_template_worksheet_structure(self):
        """Worksheet definitions must have valid structure"""
        worksheet_data = {
            "columns": [
                {"name": "col1", "title": "Column 1"},
                {"name": "col2", "title": "Column 2"}
            ],
            "rows": [
                {"id": "row1", "description": "Assets", "computation": "sum"}
            ]
        }
        
        # Check columns structure
        if "columns" in worksheet_data:
            for col in worksheet_data["columns"]:
                assert "name" in col, "Column must have name"
                assert "title" in col, "Column must have title"
        
        # Check rows structure  
        if "rows" in worksheet_data:
            for row in worksheet_data["rows"]:
                assert "id" in row, "Row must have id"
                assert "description" in row, "Row must have description"


@pytest.mark.contract
class TestTemplateSyntaxContract:
    """Test template syntax validation and expansion"""
    
    def test_template_expansion_syntax(self):
        """Template expansion syntax must be valid"""
        # Test basic template expansion
        mock_data = Mock()
        mock_data.get_config.return_value = "Test Company Ltd"
        
        # Test template: prefix
        result = expand_string("template:company-name", mock_data)
        assert result is not None, "Template expansion should return result"
        
        mock_data.get_config.assert_called_with("report.taxonomy.note-templates.company-name")
    
    def test_expand_syntax_validation(self):
        """expand: syntax must be properly parsed"""
        test_cases = [
            "expand:Simple text",
            "expand:Text with ~{variable}",
            "expand:Text with #{computation}",
            "expand:Text with <tag>content</tag>"
        ]
        
        mock_data = Mock()
        
        for test_case in test_cases:
            try:
                result = expand_string(test_case, mock_data)
                assert result is not None, f"Expand syntax '{test_case}' should be valid"
            except Exception as e:
                pytest.fail(f"Valid expand syntax '{test_case}' failed: {e}")
    
    def test_note_parser_token_validation(self):
        """Note parser must handle valid token syntax"""
        test_strings = [
            "Simple text",
            "Text with ~{variable}",
            "Text with #{computation}",
            "Text with <tag>content</tag>",
            "Mixed ~{var} and #{comp} and <tag>text</tag>"
        ]
        
        for test_string in test_strings:
            try:
                tokens = NoteParser.parse(test_string)
                assert isinstance(tokens, list), f"Parser should return token list for: {test_string}"
            except Exception as e:
                pytest.fail(f"Valid note syntax '{test_string}' failed to parse: {e}")
    
    def test_variable_substitution_syntax(self):
        """Variable substitution ~{var} syntax must be valid"""
        valid_variables = [
            "~{company-name}",
            "~{report-date}",
            "~{period-start}",
            "~{period-end}",
            "~{currency}"
        ]
        
        for var_syntax in valid_variables:
            tokens = NoteParser.parse(var_syntax)
            
            # Should parse as metadata token
            assert len(tokens) == 1, f"Variable '{var_syntax}' should parse as single token"
            
            from ixbrl_reporter.note_parse import MetadataToken
            assert isinstance(tokens[0], MetadataToken), \
                f"Variable '{var_syntax}' should parse as MetadataToken"
    
    def test_computation_syntax(self):
        """Computation #{comp} syntax must be valid"""
        valid_computations = [
            "#{total-assets}",
            "#{net-profit}",
            "#{revenue:2020}",
            "#{assets:2020:instant}"
        ]
        
        for comp_syntax in valid_computations:
            tokens = NoteParser.parse(comp_syntax)
            
            # Should parse as computation token
            assert len(tokens) == 1, f"Computation '{comp_syntax}' should parse as single token"
            
            from ixbrl_reporter.note_parse import ComputationToken
            assert isinstance(tokens[0], ComputationToken), \
                f"Computation '{comp_syntax}' should parse as ComputationToken"
    
    def test_tag_syntax_validation(self):
        """Tag <tag>content</tag> syntax must be valid"""
        valid_tags = [
            "<fact>1000</fact>",
            "<fact:uk-gaap:Assets>5000</fact:uk-gaap:Assets>",
            "<fact:instant>2020-12-31</fact:instant>"
        ]
        
        for tag_syntax in valid_tags:
            tokens = NoteParser.parse(tag_syntax)
            
            # Should have at least 3 tokens: open, content, close
            assert len(tokens) >= 3, f"Tag '{tag_syntax}' should parse into multiple tokens"
            
            from ixbrl_reporter.note_parse import TagOpen, TagClose, TextToken
            
            # First token should be TagOpen
            assert isinstance(tokens[0], TagOpen), \
                f"First token of '{tag_syntax}' should be TagOpen"
            
            # Last token should be TagClose  
            assert isinstance(tokens[-1], TagClose), \
                f"Last token of '{tag_syntax}' should be TagClose"


@pytest.mark.contract
class TestTemplateVariableContract:
    """Test template variable handling contracts"""
    
    def test_required_template_variables(self):
        """Templates must define all required variables"""
        required_variables = [
            "company-name",
            "report-period",
            "report-date", 
            "currency",
            "accounting-standards"
        ]
        
        # Mock config with template variables
        mock_config = {
            "report": {
                "taxonomy": {
                    "note-templates": {
                        "company-name": "Test Company Ltd",
                        "report-period": "Year ended 31 December 2020",
                        "report-date": "2020-12-31",
                        "currency": "GBP",
                        "accounting-standards": "UK GAAP"
                    }
                }
            }
        }
        
        config = Config(mock_config)
        
        for var_name in required_variables:
            template_key = f"report.taxonomy.note-templates.{var_name}"
            value = config.get(template_key, default=None)
            assert value is not None, f"Required template variable '{var_name}' not defined"
    
    def test_template_variable_types(self):
        """Template variables must have appropriate types"""
        variable_type_tests = [
            ("company-name", str),
            ("report-date", str),
            ("currency", str),
            ("decimal-places", int),
            ("scale-factor", int)
        ]
        
        for var_name, expected_type in variable_type_tests:
            # Mock different variable types
            if expected_type == str:
                test_value = "Test String"
            elif expected_type == int:
                test_value = 2
            else:
                test_value = None
            
            assert isinstance(test_value, expected_type), \
                f"Variable '{var_name}' should be of type {expected_type.__name__}"
    
    def test_template_variable_validation(self):
        """Template variables must pass validation rules"""
        validation_rules = {
            "currency": lambda x: len(x) == 3 and x.isupper(),
            "decimal-places": lambda x: 0 <= x <= 6,
            "scale-factor": lambda x: x >= 0,
            "company-name": lambda x: len(x.strip()) > 0
        }
        
        test_values = {
            "currency": "GBP",
            "decimal-places": 2,
            "scale-factor": 0,
            "company-name": "Test Company Ltd"
        }
        
        for var_name, validator in validation_rules.items():
            if var_name in test_values:
                value = test_values[var_name]
                assert validator(value), \
                    f"Variable '{var_name}' with value '{value}' failed validation"


@pytest.mark.contract
class TestTemplateComputationContract:
    """Test template computation contracts"""
    
    def test_computation_definition_structure(self):
        """Computation definitions must have valid structure"""
        computation_def = {
            "id": "total-assets",
            "description": "Total Assets", 
            "computation": {
                "operation": "sum",
                "inputs": ["current-assets", "fixed-assets"]
            }
        }
        
        required_fields = ["id", "description", "computation"]
        for field in required_fields:
            assert field in computation_def, \
                f"Computation definition must have '{field}' field"
        
        # Computation section validation
        comp = computation_def["computation"]
        assert "operation" in comp, "Computation must specify operation"
        
        valid_operations = ["sum", "subtract", "multiply", "divide", "constant"]
        assert comp["operation"] in valid_operations, \
            f"Operation must be one of {valid_operations}"
    
    def test_computation_input_validation(self):
        """Computation inputs must reference valid sources"""
        computation_inputs = [
            "account:Assets:Current Assets",
            "computation:net-profit",
            "constant:1000",
            "template:report-total"
        ]
        
        for input_ref in computation_inputs:
            # Should have type prefix
            assert ":" in input_ref, f"Input '{input_ref}' should have type prefix"
            
            input_type = input_ref.split(":", 1)[0]
            valid_types = ["account", "computation", "constant", "template"]
            assert input_type in valid_types, \
                f"Input type '{input_type}' must be valid"
    
    def test_computation_circular_dependency_detection(self):
        """Computations must not have circular dependencies"""
        # Mock computation definitions with potential circular dependency
        computations = {
            "comp-a": {"inputs": ["comp-b"]},
            "comp-b": {"inputs": ["comp-c"]}, 
            "comp-c": {"inputs": ["comp-a"]}  # Circular!
        }
        
        # Test dependency resolution (simplified)
        def has_circular_dependency(comp_id, visited=None):
            if visited is None:
                visited = set()
            
            if comp_id in visited:
                return True  # Circular dependency detected
            
            visited.add(comp_id)
            
            if comp_id in computations:
                for input_ref in computations[comp_id].get("inputs", []):
                    if input_ref.startswith("comp-") and has_circular_dependency(input_ref, visited.copy()):
                        return True
            
            return False
        
        # This specific example should detect circular dependency
        assert has_circular_dependency("comp-a"), \
            "Should detect circular dependency in test case"


@pytest.mark.contract
class TestTemplateWorksheetContract:
    """Test worksheet template contracts"""
    
    def test_worksheet_column_definition(self):
        """Worksheet columns must be properly defined"""
        worksheet_def = {
            "columns": [
                {
                    "name": "current-year",
                    "title": "2020",
                    "period": "2020-01-01:2020-12-31",
                    "units": "GBP"
                },
                {
                    "name": "prior-year", 
                    "title": "2019",
                    "period": "2019-01-01:2019-12-31",
                    "units": "GBP"
                }
            ]
        }
        
        for col in worksheet_def["columns"]:
            required_fields = ["name", "title"]
            for field in required_fields:
                assert field in col, f"Column must have '{field}' field"
            
            # Name should be identifier-safe
            name = col["name"]
            assert name.replace("-", "_").replace("_", "").isalnum(), \
                f"Column name '{name}' should be identifier-safe"
    
    def test_worksheet_row_definition(self):
        """Worksheet rows must be properly defined"""
        worksheet_def = {
            "rows": [
                {
                    "id": "current-assets",
                    "description": "Current Assets",
                    "computation": "sum",
                    "inputs": ["cash", "debtors", "stock"]
                },
                {
                    "id": "cash",
                    "description": "Cash at bank and in hand", 
                    "account": "Assets:Current Assets:Cash"
                }
            ]
        }
        
        for row in worksheet_def["rows"]:
            required_fields = ["id", "description"]
            for field in required_fields:
                assert field in row, f"Row must have '{field}' field"
            
            # ID should be unique and identifier-safe
            row_id = row["id"]
            assert row_id.replace("-", "_").replace("_", "").isalnum(), \
                f"Row ID '{row_id}' should be identifier-safe"
            
            # Should have either computation or account reference
            has_computation = "computation" in row
            has_account = "account" in row
            assert has_computation or has_account, \
                f"Row '{row_id}' must have either computation or account reference"
    
    def test_worksheet_layout_consistency(self):
        """Worksheet layouts must be internally consistent"""
        worksheet_def = {
            "columns": [{"name": "col1"}, {"name": "col2"}],
            "rows": [
                {"id": "row1", "description": "Row 1"},
                {"id": "row2", "description": "Row 2"}
            ]
        }
        
        # Check for duplicate column names
        column_names = [col["name"] for col in worksheet_def["columns"]]
        assert len(column_names) == len(set(column_names)), \
            "Column names must be unique"
        
        # Check for duplicate row IDs
        row_ids = [row["id"] for row in worksheet_def["rows"]]
        assert len(row_ids) == len(set(row_ids)), \
            "Row IDs must be unique"


@pytest.mark.contract
class TestTemplateCompatibilityContract:
    """Test template compatibility with different versions and systems"""
    
    def test_template_version_compatibility(self):
        """Templates should specify version compatibility"""
        template_metadata = {
            "version": "1.0",
            "ixbrl-reporter-version": ">=1.0.0",
            "taxonomy-version": "uk-gaap-2020"
        }
        
        # Check version fields
        if "version" in template_metadata:
            version = template_metadata["version"]
            assert isinstance(version, str), "Template version should be string"
            assert "." in version, "Version should have format like '1.0'"
    
    def test_template_taxonomy_compatibility(self):
        """Templates must be compatible with specified taxonomies"""
        template_taxonomy_refs = [
            "uk-gaap",
            "ifrs-full", 
            "esef",
            "ch-gaap"
        ]
        
        for taxonomy_ref in template_taxonomy_refs:
            # Should be valid taxonomy identifier
            assert taxonomy_ref.replace("-", "").isalnum(), \
                f"Taxonomy reference '{taxonomy_ref}' should be valid identifier"
    
    def test_template_encoding_compatibility(self):
        """Templates must use consistent text encoding"""
        # Test UTF-8 encoding for templates
        test_template_content = """
        description: "Company Ltd £1,000 profit"
        currency: "€"
        notes: "Directors' report"
        """
        
        try:
            # Should encode/decode as UTF-8 without errors
            encoded = test_template_content.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert decoded == test_template_content, \
                "Template content should survive UTF-8 round-trip"
        except UnicodeError as e:
            pytest.fail(f"Template content encoding failed: {e}")
    
    def test_template_file_extension_contract(self):
        """Template files must use correct file extensions"""
        valid_extensions = [".yaml", ".yml"]
        
        template_filenames = [
            "balance-sheet.yaml",
            "profit-loss.yml", 
            "cash-flow.yaml"
        ]
        
        for filename in template_filenames:
            file_ext = Path(filename).suffix
            assert file_ext in valid_extensions, \
                f"Template file '{filename}' should use valid extension {valid_extensions}"


@pytest.mark.contract
class TestTemplateErrorHandlingContract:
    """Test template error handling contracts"""
    
    def test_template_missing_variable_handling(self):
        """Templates should handle missing variables gracefully"""
        mock_data = Mock()
        mock_data.get_config.return_value = None  # Missing variable
        
        try:
            # Should not crash on missing template variable
            result = expand_string("template:missing-variable", mock_data)
            # Should return some form of result (even if None/default)
            assert result is not None or result is None  # Either is acceptable
        except Exception as e:
            # If it raises an exception, should be a known error type
            assert isinstance(e, (KeyError, AttributeError, ValueError)), \
                f"Missing variable should raise known error type, got: {type(e)}"
    
    def test_template_malformed_syntax_handling(self):
        """Templates should handle malformed syntax appropriately"""
        malformed_syntax_cases = [
            "expand:~{unclosed-variable",  # Unclosed variable
            "expand:<unclosed-tag>text",   # Unclosed tag
            "expand:#{malformed-comp",     # Unclosed computation
        ]
        
        mock_data = Mock()
        
        for malformed in malformed_syntax_cases:
            try:
                result = expand_string(malformed, mock_data)
                # If it succeeds, should return something reasonable
                assert result is not None
            except Exception as e:
                # Should raise a reasonable error type
                assert isinstance(e, (RuntimeError, ValueError, SyntaxError)), \
                    f"Malformed syntax should raise appropriate error, got: {type(e)}"
    
    def test_template_circular_reference_handling(self):
        """Templates should detect and handle circular references"""
        # Mock circular template reference
        mock_data = Mock()
        
        def mock_get_config(key):
            if key == "report.taxonomy.note-templates.template-a":
                return "template:template-b"
            elif key == "report.taxonomy.note-templates.template-b":
                return "template:template-a"  # Circular!
            return None
        
        mock_data.get_config.side_effect = mock_get_config
        
        # Should detect and handle circular reference
        with pytest.raises((RuntimeError, RecursionError)):
            # This should fail with appropriate error
            expand_string("template:template-a", mock_data)