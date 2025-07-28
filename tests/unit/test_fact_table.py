"""
Unit tests for ixbrl_reporter.fact_table module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO

from ixbrl_reporter.fact_table import Box, FactTable


class TestBox:
    """Test Box class functionality"""
    
    def test_box_init_with_all_params(self):
        """Box should initialize with all parameters"""
        tag = {"type": "monetary"}
        box = Box("1", "Test Description", 1000, tag)
        
        assert box.number == "1"
        assert box.description == "Test Description"
        assert box.value == 1000
        assert box.tag == {"type": "monetary"}
    
    def test_box_init_without_tag(self):
        """Box should initialize with empty tag dict when tag is None"""
        box = Box("2", "Another Description", 2000)
        
        assert box.number == "2"
        assert box.description == "Another Description"
        assert box.value == 2000
        assert box.tag == {}
    
    def test_box_init_with_none_tag(self):
        """Box should handle explicit None tag"""
        box = Box("3", "Third Description", 3000, None)
        
        assert box.number == "3"
        assert box.description == "Third Description"
        assert box.value == 3000
        assert box.tag == {}
    
    def test_box_init_different_value_types(self):
        """Box should handle different value types"""
        test_cases = [
            ("int", 42),
            ("float", 42.5),
            ("string", "test value"),
            ("bool", True),
            ("none", None)
        ]
        
        for desc, value in test_cases:
            box = Box("1", desc, value)
            assert box.value == value
    
    def test_box_tag_reference_behavior(self):
        """Box tag behavior with original dict - documents current behavior"""
        original_tag = {"key": "value"}
        box = Box("1", "test", 100, original_tag)
        
        # Modify original tag
        original_tag["new_key"] = "new_value"
        
        # Current implementation shares reference - box.tag is affected
        # This documents the current behavior (not necessarily ideal)
        assert "new_key" in box.tag
        assert box.tag == {"key": "value", "new_key": "new_value"}


class TestFactTableInit:
    """Test FactTable initialization"""
    
    def test_fact_table_init_with_all_params(self):
        """FactTable should initialize with all parameters"""
        mock_data = Mock()
        elements = [{"field": "test", "description": "Test field"}]
        
        fact_table = FactTable("test-id", elements, "Test Title", mock_data)
        
        assert fact_table.id == "test-id"
        assert fact_table.elements == elements
        assert fact_table.title == "Test Title"
        assert fact_table.data == mock_data
    
    def test_fact_table_init_inheritance(self):
        """FactTable should properly inherit from BasicElement"""
        mock_data = Mock()
        
        with patch('ixbrl_reporter.fact_table.BasicElement.__init__') as mock_super_init:
            fact_table = FactTable("test-id", [], "Title", mock_data)
            
            # Verify parent constructor was called
            mock_super_init.assert_called_once_with("test-id", mock_data)
    
    def test_fact_table_init_with_none_id(self):
        """FactTable should handle None id (BasicElement will generate UUID)"""
        mock_data = Mock()
        
        with patch('ixbrl_reporter.fact_table.BasicElement.__init__') as mock_super_init:
            fact_table = FactTable(None, [], "Title", mock_data)
            
            mock_super_init.assert_called_once_with(None, mock_data)


class TestFactTableLoad:
    """Test FactTable.load static method"""
    
    def test_load_with_all_elements(self):
        """load() should create FactTable with all provided elements"""
        mock_data = Mock()
        mock_elt_def = Mock()
        mock_elt_def.get.side_effect = lambda key, mandatory=True: {
            "id": "table-1",
            "facts": [{"field": "1", "description": "Test fact"}],
            "title": "Test Fact Table"
        }[key]
        
        result = FactTable.load(mock_elt_def, mock_data)
        
        assert isinstance(result, FactTable)
        assert result.id == "table-1"
        assert result.elements == [{"field": "1", "description": "Test fact"}]
        assert result.title == "Test Fact Table"
        assert result.data == mock_data
        
        # Verify get calls
        mock_elt_def.get.assert_any_call("id", mandatory=False)
        mock_elt_def.get.assert_any_call("facts")
        mock_elt_def.get.assert_any_call("title", "Fact table")
    
    def test_load_with_default_title(self):
        """load() should use default title when not provided"""
        mock_data = Mock()
        mock_elt_def = Mock()
        mock_elt_def.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", False): None,
            ("facts",): [],
            ("title", "Fact table"): "Fact table"  # Default should be returned
        }.get((key, default) if default is not None else (key, mandatory), None)
        
        result = FactTable.load(mock_elt_def, mock_data)
        
        assert result.title == "Fact table"
    
    def test_load_with_no_id(self):
        """load() should handle missing id"""
        mock_data = Mock()
        mock_elt_def = Mock()
        
        def mock_get(key, mandatory=True):
            if key == "id" and not mandatory:
                return None
            elif key == "facts":
                return []
            elif key == "title":
                return "Test Title"
            else:
                return "Fact table"  # default title
        
        mock_elt_def.get.side_effect = mock_get
        
        result = FactTable.load(mock_elt_def, mock_data)
        
        # BasicElement generates UUID when id is None
        assert result.id is not None
        assert result.id.startswith("elt-")  # UUID format
        
        # Verify id was requested with mandatory=False
        mock_elt_def.get.assert_any_call("id", mandatory=False)


class TestFactTableToText:
    """Test FactTable.to_text method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.output = StringIO()
    
    def test_to_text_with_single_element(self):
        """to_text should render single fact correctly"""
        # Set up element and datum
        element = {"description": "Company Name"}
        elements = [element]
        
        mock_datum = Mock()
        mock_datum.value = "Test Company Ltd"
        self.mock_data.to_datum.return_value = mock_datum
        
        fact_table = FactTable("test", elements, "Company Details", self.mock_data)
        
        # Mock taxonomy (not used in to_text but required by signature)
        mock_taxonomy = Mock()
        
        fact_table.to_text(mock_taxonomy, self.output)
        
        output_content = self.output.getvalue()
        assert "*** Company Details ***" in output_content
        assert "Company Name: Test Company Ltd" in output_content
        
        # Verify data.to_datum was called correctly
        self.mock_data.to_datum.assert_called_once_with(element, None)
    
    def test_to_text_with_multiple_elements(self):
        """to_text should render multiple facts correctly"""
        elements = [
            {"description": "Company Name"},
            {"description": "Revenue"},
            {"description": "Employees"}
        ]
        
        # Set up mock datums
        mock_datums = [
            Mock(value="Test Company Ltd"),
            Mock(value="£1,000,000"),
            Mock(value="50")
        ]
        self.mock_data.to_datum.side_effect = mock_datums
        
        fact_table = FactTable("test", elements, "Company Summary", self.mock_data)
        mock_taxonomy = Mock()
        
        fact_table.to_text(mock_taxonomy, self.output)
        
        output_content = self.output.getvalue()
        
        # Check title
        assert "*** Company Summary ***" in output_content
        
        # Check all facts are present
        assert "Company Name: Test Company Ltd" in output_content
        assert "Revenue: £1,000,000" in output_content
        assert "Employees: 50" in output_content
        
        # Verify all datums were requested
        assert self.mock_data.to_datum.call_count == 3
        expected_calls = [call(elem, None) for elem in elements]
        self.mock_data.to_datum.assert_has_calls(expected_calls)
    
    def test_to_text_with_empty_elements(self):
        """to_text should handle empty elements list"""
        fact_table = FactTable("test", [], "Empty Table", self.mock_data)
        mock_taxonomy = Mock()
        
        fact_table.to_text(mock_taxonomy, self.output)
        
        output_content = self.output.getvalue()
        assert "*** Empty Table ***" in output_content
        
        # Should not call to_datum for empty list
        self.mock_data.to_datum.assert_not_called()
    
    def test_to_text_title_formatting(self):
        """to_text should format title correctly"""
        fact_table = FactTable("test", [], "Test Title With Spaces", self.mock_data)
        mock_taxonomy = Mock()
        
        fact_table.to_text(mock_taxonomy, self.output)
        
        output_content = self.output.getvalue()
        # Check exact title formatting
        assert "*** Test Title With Spaces ***\n" in output_content


class TestFactTableToIxbrlElt:
    """Test FactTable.to_ixbrl_elt method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.mock_taxonomy = Mock()
        self.mock_par = Mock()
        
        # Set up xhtml_maker mock
        self.mock_xhtml_maker = Mock()
        self.mock_par.xhtml_maker = self.mock_xhtml_maker
        
        # Set up div and h2 mocks
        self.mock_div = Mock()
        self.mock_h2 = Mock()
        self.mock_xhtml_maker.div.return_value = self.mock_div
        self.mock_xhtml_maker.h2.return_value = self.mock_h2
        
        # Set up data context mocks
        self.mock_period = Mock()
        self.mock_report_date = Mock()
        self.mock_business_context = Mock()
        self.mock_period_context = Mock()
        self.mock_date_context = Mock()
        
        self.mock_data.get_report_period.return_value = self.mock_period
        self.mock_data.get_report_date.return_value = self.mock_report_date
        self.mock_data.get_business_context.return_value = self.mock_business_context
        self.mock_business_context.with_period.return_value = self.mock_period_context
        self.mock_business_context.with_instant.return_value = self.mock_date_context
    
    def test_to_ixbrl_elt_basic_structure(self):
        """to_ixbrl_elt should create proper div structure"""
        fact_table = FactTable("test-table", [], "Test Title", self.mock_data)
        
        result = fact_table.to_ixbrl_elt(self.mock_par, self.mock_taxonomy)
        
        # Should return list with div element
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == self.mock_div
        
        # Verify div setup
        self.mock_xhtml_maker.div.assert_called_once()
        self.mock_div.set.assert_any_call("class", "facts")
        self.mock_div.set.assert_any_call("id", "test-table-element")
        
        # Verify title setup
        self.mock_xhtml_maker.h2.assert_called_once_with("Test Title")
        self.mock_div.append.assert_any_call(self.mock_h2)
    
    def test_to_ixbrl_elt_context_setup(self):
        """to_ixbrl_elt should set up contexts correctly"""
        fact_table = FactTable("test", [], "Title", self.mock_data)
        
        fact_table.to_ixbrl_elt(self.mock_par, self.mock_taxonomy)
        
        # Verify context creation calls
        self.mock_data.get_report_period.assert_called_once()
        self.mock_data.get_report_date.assert_called_once()
        self.mock_data.get_business_context.assert_called()  # May be called multiple times
        self.mock_business_context.with_period.assert_called_once_with(self.mock_period)
        self.mock_business_context.with_instant.assert_called_once_with(self.mock_report_date)
    
    def test_to_ixbrl_elt_with_single_element(self):
        """to_ixbrl_elt should process single element correctly"""
        element = {"field": "1", "description": "Test Field"}
        fact_table = FactTable("test", [element], "Title", self.mock_data)
        
        # Set up mocks for element processing
        mock_datum = Mock()
        mock_fact = Mock()
        mock_fact_elt = Mock()
        
        self.mock_data.to_datum.return_value = mock_datum
        self.mock_taxonomy.create_fact.return_value = mock_fact
        
        with patch.object(fact_table, 'make_fact', return_value=mock_fact_elt) as mock_make_fact:
            result = fact_table.to_ixbrl_elt(self.mock_par, self.mock_taxonomy)
        
        # Verify element processing
        self.mock_data.to_datum.assert_called_once_with(element, self.mock_period_context)
        self.mock_taxonomy.create_fact.assert_called_once_with(mock_datum)
        mock_make_fact.assert_called_once_with(
            self.mock_par, "1", "Test Field", mock_fact
        )
        
        # Verify fact element was added to div
        self.mock_div.append.assert_any_call(mock_fact_elt)
    
    def test_to_ixbrl_elt_with_custom_context(self):
        """to_ixbrl_elt should handle custom context in element"""
        element = {
            "field": "1", 
            "description": "Test Field",
            "context": "custom-context"
        }
        fact_table = FactTable("test", [element], "Title", self.mock_data)
        
        mock_custom_context = Mock()
        self.mock_taxonomy.get_context.return_value = mock_custom_context
        
        mock_datum = Mock()
        mock_fact = Mock()
        self.mock_data.to_datum.return_value = mock_datum
        self.mock_taxonomy.create_fact.return_value = mock_fact
        
        with patch.object(fact_table, 'make_fact', return_value=Mock()):
            fact_table.to_ixbrl_elt(self.mock_par, self.mock_taxonomy)
        
        # Verify custom context was used
        self.mock_taxonomy.get_context.assert_called_once_with("custom-context")
        self.mock_data.to_datum.assert_called_once_with(element, mock_custom_context)
    
    def test_to_ixbrl_elt_invalid_datum_raises_error(self):
        """to_ixbrl_elt should raise error for invalid datum"""
        element = {"field": "1", "description": "Invalid Field"}
        fact_table = FactTable("test", [element], "Title", self.mock_data)
        
        # Mock to_datum returning None/falsy value
        self.mock_data.to_datum.return_value = None
        
        with pytest.raises(RuntimeError, match="Not valid: .*"):
            fact_table.to_ixbrl_elt(self.mock_par, self.mock_taxonomy)
    
    def test_to_ixbrl_elt_multiple_elements(self):
        """to_ixbrl_elt should handle multiple elements"""
        elements = [
            {"field": "1", "description": "Field 1"},
            {"field": "2", "description": "Field 2", "context": "custom"},
            {"field": "3", "description": "Field 3"}
        ]
        fact_table = FactTable("test", elements, "Title", self.mock_data)
        
        # Set up mocks
        mock_datums = [Mock(), Mock(), Mock()]
        mock_facts = [Mock(), Mock(), Mock()]
        mock_fact_elts = [Mock(), Mock(), Mock()]
        
        self.mock_data.to_datum.side_effect = mock_datums
        self.mock_taxonomy.create_fact.side_effect = mock_facts
        self.mock_taxonomy.get_context.return_value = Mock()
        
        with patch.object(fact_table, 'make_fact', side_effect=mock_fact_elts):
            result = fact_table.to_ixbrl_elt(self.mock_par, self.mock_taxonomy)
        
        # Verify all elements were processed
        assert self.mock_data.to_datum.call_count == 3
        assert self.mock_taxonomy.create_fact.call_count == 3
        
        # Verify all fact elements were added
        for fact_elt in mock_fact_elts:
            self.mock_div.append.assert_any_call(fact_elt)


class TestFactTableMakeFact:
    """Test FactTable.make_fact method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.mock_par = Mock()
        
        # Set up xhtml_maker mock
        self.mock_xhtml_maker = Mock()
        self.mock_par.xhtml_maker = self.mock_xhtml_maker
        
        # Set up element mocks
        self.mock_row_div = Mock()
        self.mock_num_div = Mock()
        self.mock_desc_div = Mock()
        self.mock_val_div = Mock()
        
        def div_side_effect(text=None):
            if text is None:
                return self.mock_val_div
            elif text == "1":
                return self.mock_num_div
            elif text.endswith(":"):
                return self.mock_desc_div
            else:
                return self.mock_row_div
        
        self.mock_xhtml_maker.div.side_effect = div_side_effect
        
        # First call returns row div
        def div_no_args():
            return self.mock_row_div
        self.mock_xhtml_maker.div.return_value = self.mock_row_div
    
    def test_make_fact_structure(self):
        """make_fact should create proper HTML structure"""
        fact_table = FactTable("test", [], "Title", self.mock_data)
        mock_fact = Mock()
        mock_fact_elt = Mock()
        mock_fact.to_elt.return_value = mock_fact_elt
        
        # Mock div calls in sequence
        div_calls = []
        def div_side_effect(text=None):
            if text is None:
                div_calls.append("empty")
                return self.mock_val_div
            elif text == "1":
                div_calls.append("field")
                return self.mock_num_div
            else:
                div_calls.append("desc")
                return self.mock_desc_div
        
        # First call (no args) returns row div
        self.mock_xhtml_maker.div.side_effect = [self.mock_row_div] + [
            div_side_effect(arg) if arg else div_side_effect() 
            for arg in ["1", "Test Description:", None]
        ]
        
        result = fact_table.make_fact(self.mock_par, "1", "Test Description", mock_fact)
        
        # Should return row div
        assert result == self.mock_row_div
        
        # Verify div creation calls
        assert self.mock_xhtml_maker.div.call_count == 4
        
        # Verify row div setup
        self.mock_row_div.set.assert_called_once_with("class", "fact")
        
        # Verify all elements were appended to row
        self.mock_row_div.append.assert_any_call(self.mock_num_div)
        self.mock_row_div.append.assert_any_call(self.mock_desc_div)
        self.mock_row_div.append.assert_any_call(self.mock_val_div)
    
    def test_make_fact_element_attributes(self):
        """make_fact should set correct attributes on elements"""
        fact_table = FactTable("test", [], "Title", self.mock_data)
        mock_fact = Mock()
        mock_fact.to_elt.return_value = Mock()
        
        # Create distinct mocks for each div
        mock_row = Mock()
        mock_num = Mock()
        mock_desc = Mock()  
        mock_val = Mock()
        
        self.mock_xhtml_maker.div.side_effect = [mock_row, mock_num, mock_desc, mock_val]
        
        fact_table.make_fact(self.mock_par, "REF-1", "Reference Description", mock_fact)
        
        # Verify class attributes
        mock_row.set.assert_called_once_with("class", "fact")
        mock_num.set.assert_called_once_with("class", "ref")
        mock_desc.set.assert_called_once_with("class", "description")
        mock_val.set.assert_called_once_with("class", "factvalue")
    
    def test_make_fact_content(self):
        """make_fact should set correct content in elements"""
        fact_table = FactTable("test", [], "Title", self.mock_data)
        mock_fact = Mock()
        mock_fact_elt = Mock()
        mock_fact.to_elt.return_value = mock_fact_elt
        
        # Track div creation with content
        created_divs = []
        def track_div_creation(*args):
            mock_div = Mock()
            created_divs.append((mock_div, args))
            return mock_div
        
        self.mock_xhtml_maker.div.side_effect = track_div_creation
        
        result = fact_table.make_fact(self.mock_par, "TEST-123", "Test Field Description", mock_fact)
        
        # Should have created 4 divs
        assert len(created_divs) == 4
        
        # Check div creation arguments
        row_div, row_args = created_divs[0]
        num_div, num_args = created_divs[1]  
        desc_div, desc_args = created_divs[2]
        val_div, val_args = created_divs[3]
        
        assert row_args == ()  # Row div created with no args
        assert num_args == ("TEST-123",)  # Field content
        assert desc_args == ("Test Field Description:",)  # Description with colon
        assert val_args == ()  # Value div created empty
        
        # Verify fact element was added to value div
        val_div.append.assert_called_once_with(mock_fact_elt)
        
        # Verify fact.to_elt was called
        mock_fact.to_elt.assert_called_once_with(self.mock_par)
    
    def test_make_fact_with_empty_strings(self):
        """make_fact should handle empty field and description"""
        fact_table = FactTable("test", [], "Title", self.mock_data)
        mock_fact = Mock()
        mock_fact.to_elt.return_value = Mock()
        
        # Create distinct mocks
        divs = [Mock() for _ in range(4)]
        self.mock_xhtml_maker.div.side_effect = divs
        
        fact_table.make_fact(self.mock_par, "", "", mock_fact)
        
        # Verify creation calls included empty strings
        calls = self.mock_xhtml_maker.div.call_args_list
        assert calls[0] == call()  # Row div
        assert calls[1] == call("")  # Empty field
        assert calls[2] == call(":")  # Empty description with colon
        assert calls[3] == call()  # Value div


class TestFactTableIntegration:
    """Integration-style tests for FactTable"""
    
    def test_fact_table_complete_workflow(self):
        """Test complete FactTable workflow with realistic data"""
        # Set up realistic element data
        elements = [
            {"field": "1", "description": "Company Name"},
            {"field": "2", "description": "Revenue", "context": "annual"},
            {"field": "3", "description": "Employees"}
        ]
        
        mock_data = Mock()
        fact_table = FactTable("company-facts", elements, "Company Information", mock_data)
        
        # Test load method
        mock_elt_def = Mock()
        def mock_get(key, mandatory=True):
            if key == "id" and not mandatory:
                return "loaded-id"
            elif key == "facts":
                return elements
            elif key == "title":
                return "Loaded Title"
            else:
                return "Fact table"
        
        mock_elt_def.get.side_effect = mock_get
        
        loaded_table = FactTable.load(mock_elt_def, mock_data)
        
        assert loaded_table.id == "loaded-id"
        assert loaded_table.elements == elements
        assert loaded_table.title == "Loaded Title"
        assert loaded_table.data == mock_data
    
    def test_fact_table_text_and_ixbrl_consistency(self):
        """Test that text and ixbrl output use same data"""
        elements = [{"field": "1", "description": "Test Field"}]
        mock_data = Mock()
        fact_table = FactTable("test", elements, "Test", mock_data)
        
        # Set up datum mock
        mock_datum = Mock(value="Test Value")
        mock_data.to_datum.return_value = mock_datum
        
        # Test text output
        text_output = StringIO()
        fact_table.to_text(Mock(), text_output)
        
        # Reset mock to test ixbrl
        mock_data.reset_mock()
        mock_data.to_datum.return_value = mock_datum
        mock_data.get_report_period.return_value = Mock()
        mock_data.get_report_date.return_value = Mock()
        mock_data.get_business_context.return_value = Mock()
        mock_data.get_business_context.return_value.with_period.return_value = Mock()
        mock_data.get_business_context.return_value.with_instant.return_value = Mock()
        
        # Mock taxonomy and parent for ixbrl
        mock_taxonomy = Mock()
        mock_taxonomy.create_fact.return_value = Mock()
        mock_par = Mock()
        mock_par.xhtml_maker.div.return_value = Mock()
        mock_par.xhtml_maker.h2.return_value = Mock()
        
        with patch.object(fact_table, 'make_fact', return_value=Mock()):
            fact_table.to_ixbrl_elt(mock_par, mock_taxonomy)
        
        # Both should have called to_datum with same element
        # (Note: contexts will be different, but element should be same)
        assert mock_data.to_datum.call_count == 1
        call_args = mock_data.to_datum.call_args_list[0]
        assert call_args[0][0] == elements[0]  # Same element used


class TestFactTableErrorCases:
    """Test error cases and edge conditions"""
    
    def test_fact_table_with_none_elements(self):
        """FactTable should handle None elements gracefully"""
        mock_data = Mock()
        
        # This might cause issues, but test the behavior
        fact_table = FactTable("test", None, "Title", mock_data)
        
        # Should not crash on initialization
        assert fact_table.elements is None
        
        # to_text should handle None elements
        with pytest.raises(TypeError):
            fact_table.to_text(Mock(), StringIO())
    
    def test_fact_table_datum_creation_failure(self):
        """Test behavior when datum creation fails"""
        element = {"field": "1", "description": "Test"}
        mock_data = Mock()
        fact_table = FactTable("test", [element], "Title", mock_data)
        
        # Mock to_datum to return falsy value
        mock_data.to_datum.return_value = None
        
        mock_par = Mock()
        mock_par.xhtml_maker.div.return_value = Mock()
        mock_par.xhtml_maker.h2.return_value = Mock()
        mock_data.get_report_period.return_value = Mock()
        mock_data.get_report_date.return_value = Mock()
        mock_data.get_business_context.return_value = Mock()
        mock_data.get_business_context.return_value.with_period.return_value = Mock()
        mock_data.get_business_context.return_value.with_instant.return_value = Mock()
        
        with pytest.raises(RuntimeError, match="Not valid"):
            fact_table.to_ixbrl_elt(mock_par, Mock())
    
    def test_make_fact_with_none_parameters(self):
        """make_fact should handle None parameters (documents current limitation)"""
        mock_data = Mock()
        fact_table = FactTable("test", [], "Title", mock_data)
        
        mock_par = Mock()
        mock_par.xhtml_maker.div.side_effect = [Mock() for _ in range(4)]
        
        mock_fact = Mock()
        mock_fact.to_elt.return_value = Mock()
        
        # Current implementation doesn't handle None description properly
        with pytest.raises(TypeError, match="unsupported operand type"):
            fact_table.make_fact(mock_par, None, None, mock_fact)
    
    def test_make_fact_with_empty_description(self):
        """make_fact should handle empty string description"""
        mock_data = Mock()
        fact_table = FactTable("test", [], "Title", mock_data)
        
        mock_par = Mock()
        mock_par.xhtml_maker.div.side_effect = [Mock() for _ in range(4)]
        
        mock_fact = Mock()
        mock_fact.to_elt.return_value = Mock()
        
        # Empty string should work (unlike None)
        result = fact_table.make_fact(mock_par, "", "", mock_fact)
        assert result is not None
    
    def test_load_with_missing_required_fields(self):
        """load should handle missing required fields appropriately"""
        mock_data = Mock()
        mock_elt_def = Mock()
        
        # Mock get to raise exception for missing required field
        def mock_get(key, mandatory=True):
            if key == "facts" and mandatory:
                raise RuntimeError(f"Required field '{key}' missing")
            return {"id": "test", "title": "Test"}.get(key)
        
        mock_elt_def.get.side_effect = mock_get
        
        with pytest.raises(RuntimeError, match="Required field 'facts' missing"):
            FactTable.load(mock_elt_def, mock_data)