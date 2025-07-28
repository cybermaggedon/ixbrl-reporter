"""
Unit tests for layout module

The layout module contains various element classes for handling XBRL report layout
and rendering in different formats (HTML, text, debug).
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from io import StringIO

from ixbrl_reporter.layout import (
    Elt, TagElt, IfdefElt, MetadataElt, StringElt, FactElt, 
    ElementElt, WorksheetElt, ComputationElt
)
from ixbrl_reporter.datum import StringDatum


class TestElt:
    """Test the base Elt class and its load factory method"""
    
    def test_load_string_input(self):
        """Test loading a string input"""
        mock_data = Mock()
        mock_data.expand_string.return_value = "expanded string"
        
        result = Elt.load("test string", mock_data)
        
        assert result == "expanded string"
        mock_data.expand_string.assert_called_once_with("test string")
    
    def test_load_tag_element(self):
        """Test loading a tag element"""
        root = {"tag": "div", "content": "test"}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.TagElt.load') as mock_load:
            mock_load.return_value = Mock()
            result = Elt.load(root, mock_data)
            
            mock_load.assert_called_once_with(root, mock_data)
    
    def test_load_fact_element(self):
        """Test loading a fact element"""
        root = {"fact": "test-fact", "content": "test"}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.FactElt.load') as mock_load:
            mock_load.return_value = Mock()
            result = Elt.load(root, mock_data)
            
            mock_load.assert_called_once_with(root, mock_data)
    
    def test_load_element_element(self):
        """Test loading an element element"""
        root = {"element": "test-element"}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.ElementElt.load') as mock_load:
            mock_load.return_value = Mock()
            result = Elt.load(root, mock_data)
            
            mock_load.assert_called_once_with(root, mock_data)
    
    def test_load_worksheet_element(self):
        """Test loading a worksheet element"""
        root = {"worksheet": "test-worksheet"}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.WorksheetElt.load') as mock_load:
            mock_load.return_value = Mock()
            result = Elt.load(root, mock_data)
            
            mock_load.assert_called_once_with(root, mock_data)
    
    def test_load_ifdef_element(self):
        """Test loading an ifdef element"""
        root = {"ifdef": "test.condition", "content": "conditional content"}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.IfdefElt.load') as mock_load:
            mock_load.return_value = Mock()
            result = Elt.load(root, mock_data)
            
            mock_load.assert_called_once_with(root, mock_data)
    
    def test_load_unknown_element_raises_error(self):
        """Test that unknown element type raises RuntimeError"""
        root = {"unknown": "test"}
        mock_data = Mock()
        
        with pytest.raises(RuntimeError, match="Can't handle"):
            Elt.load(root, mock_data)


class TestTagElt:
    """Test the TagElt class"""
    
    def test_init(self):
        """Test TagElt initialization"""
        mock_data = Mock()
        tag_elt = TagElt("div", {"class": "test"}, ["content"], mock_data)
        
        assert tag_elt.tag == "div"
        assert tag_elt.attrs == {"class": "test"}
        assert tag_elt.content == ["content"]
        assert tag_elt.data == mock_data
    
    def test_load_simple_tag(self):
        """Test loading a simple tag"""
        root = {"tag": "div", "attributes": {"class": "test"}}
        mock_data = Mock()
        
        result = TagElt.load(root, mock_data)
        
        assert isinstance(result, TagElt)
        assert result.tag == "div"
        assert result.attrs == {"class": "test"}
        assert result.content == []
    
    def test_load_with_string_content(self):
        """Test loading tag with string content"""
        root = {"tag": "div", "content": "test content"}
        mock_data = Mock()
        mock_data.expand_string.return_value = "expanded content"
        
        result = TagElt.load(root, mock_data)
        
        assert len(result.content) == 1
        assert result.content[0] == "expanded content"
    
    def test_load_with_list_content(self):
        """Test loading tag with list content"""
        root = {"tag": "div", "content": ["item1", "item2"]}
        mock_data = Mock()
        mock_data.expand_string.side_effect = lambda x: f"expanded {x}"
        
        result = TagElt.load(root, mock_data)
        
        assert len(result.content) == 2
        assert result.content[0] == "expanded item1"
        assert result.content[1] == "expanded item2"
    
    def test_load_with_dict_content(self):
        """Test loading tag with dict content"""
        root = {"tag": "div", "content": {"tag": "span"}}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.Elt.load') as mock_load:
            mock_load.return_value = Mock()
            result = TagElt.load(root, mock_data)
            
            assert len(result.content) == 1
            mock_load.assert_called_with({"tag": "span"}, mock_data)
    
    def test_load_with_invalid_content_type(self):
        """Test loading tag with invalid content type raises error"""
        root = {"tag": "div", "content": 123}
        mock_data = Mock()
        
        with pytest.raises(RuntimeError, match="Can't handle content being type"):
            TagElt.load(root, mock_data)
    
    def test_to_html(self):
        """Test HTML generation"""
        mock_data = Mock()
        mock_content1 = Mock()
        mock_content2 = Mock()
        mock_content1.to_html.return_value = "html1"
        mock_content2.to_html.return_value = "html2"
        
        tag_elt = TagElt("div", {"class": "test"}, [mock_content1, mock_content2], mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_element = Mock()
        mock_par.xhtml_maker.return_value = mock_element
        
        result = tag_elt.to_html(mock_par, mock_taxonomy)
        
        mock_par.xhtml_maker.assert_called_once_with("div", {"class": "test"})
        mock_element.append.assert_any_call("html1")
        mock_element.append.assert_any_call("html2")
        assert result == mock_element
    
    def test_to_html_with_none_content(self):
        """Test HTML generation with None content (should be skipped)"""
        mock_data = Mock()
        mock_content = Mock()
        mock_content.to_html.return_value = None
        
        tag_elt = TagElt("div", {}, [mock_content], mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_element = Mock()
        mock_par.xhtml_maker.return_value = mock_element
        
        result = tag_elt.to_html(mock_par, mock_taxonomy)
        
        mock_element.append.assert_not_called()
    
    def test_to_text_with_block_elements(self):
        """Test text generation with block elements"""
        mock_data = Mock()
        mock_content = Mock()
        
        for tag in ["div", "p", "td", "br", "tr", "h1", "h2", "h3"]:
            tag_elt = TagElt(tag, {}, [mock_content], mock_data)
            out = StringIO()
            
            tag_elt.to_text(Mock(), out)
            
            mock_content.to_text.assert_called()
            assert out.getvalue().endswith("\n")
    
    def test_to_text_with_hr_element(self):
        """Test text generation with hr element"""
        mock_data = Mock()
        mock_content = Mock()
        tag_elt = TagElt("hr", {}, [mock_content], mock_data)
        
        out = StringIO()
        tag_elt.to_text(Mock(), out)
        
        assert out.getvalue() == "--------\n"
    
    def test_to_debug(self):
        """Test debug output generation"""
        mock_data = Mock()
        mock_content = Mock()
        tag_elt = TagElt("div", {}, [mock_content], mock_data)
        
        with patch('builtins.print') as mock_print:
            tag_elt.to_debug(Mock(), Mock())
        
        mock_content.to_debug.assert_called()
        mock_print.assert_called_with("tag:", "div")


class TestIfdefElt:
    """Test the IfdefElt class"""
    
    def test_init(self):
        """Test IfdefElt initialization"""
        mock_content = Mock()
        mock_data = Mock()
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        
        assert ifdef_elt.key == "test.key"
        assert ifdef_elt.content == mock_content
        assert ifdef_elt.data == mock_data
    
    def test_load(self):
        """Test loading an ifdef element"""
        root = {"ifdef": "test.condition", "content": {"tag": "div"}}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.Elt.load') as mock_load:
            mock_content = Mock()
            mock_load.return_value = mock_content
            
            result = IfdefElt.load(root, mock_data)
            
            assert isinstance(result, IfdefElt)
            assert result.key == "test.condition"
            assert result.content == mock_content
            mock_load.assert_called_once_with({"tag": "div"}, mock_data)
    
    def test_to_html_condition_true(self):
        """Test HTML generation when condition is true"""
        mock_content = Mock()
        mock_content.to_html.return_value = "html_content"
        mock_data = Mock()
        mock_data.get_config.return_value = "some_value"
        
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        
        result = ifdef_elt.to_html(Mock(), Mock())
        
        assert result == "html_content"
        mock_data.get_config.assert_called_once_with("test.key")
    
    def test_to_html_condition_false(self):
        """Test HTML generation when condition is false"""
        mock_content = Mock()
        mock_data = Mock()
        mock_data.get_config.side_effect = Exception("Config not found")
        
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        
        result = ifdef_elt.to_html(Mock(), Mock())
        
        assert result is None
        mock_content.to_html.assert_not_called()
    
    def test_to_text_condition_true(self):
        """Test text generation when condition is true"""
        mock_content = Mock()
        mock_data = Mock()
        mock_data.get_config.return_value = "some_value"
        
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        out = StringIO()
        
        ifdef_elt.to_text(Mock(), out)
        
        mock_content.to_text.assert_called()
    
    def test_to_text_condition_false(self):
        """Test text generation when condition is false"""
        mock_content = Mock()
        mock_data = Mock()
        mock_data.get_config.side_effect = Exception("Config not found")
        
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        out = StringIO()
        
        ifdef_elt.to_text(Mock(), out)
        
        mock_content.to_text.assert_not_called()
    
    def test_to_debug_condition_true(self):
        """Test debug generation when condition is true"""
        mock_content = Mock()
        mock_data = Mock()
        mock_data.get_config.return_value = "some_value"
        
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        
        ifdef_elt.to_debug(Mock(), Mock())
        
        mock_content.to_debug.assert_called()
    
    def test_to_debug_condition_false(self):
        """Test debug generation when condition is false"""
        mock_content = Mock()
        mock_data = Mock()
        mock_data.get_config.side_effect = Exception("Config not found")
        
        ifdef_elt = IfdefElt("test.key", mock_content, mock_data)
        
        ifdef_elt.to_debug(Mock(), Mock())
        
        mock_content.to_debug.assert_not_called()


class TestMetadataElt:
    """Test the MetadataElt class"""
    
    def test_init(self):
        """Test MetadataElt initialization"""
        mock_data = Mock()
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null_value", mock_data)
        
        assert meta_elt.name == "test.name"
        assert meta_elt.prefix == "prefix:"
        assert meta_elt.suffix == ":suffix"
        assert meta_elt.null == "null_value"
        assert meta_elt.data == mock_data
    
    def test_to_html_with_taxonomy_fact(self):
        """Test HTML generation with taxonomy fact"""
        mock_data = Mock()
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null", mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_fact = Mock()
        mock_fact.to_elt.return_value = "fact_element"
        mock_taxonomy.get_metadata_by_id.return_value = mock_fact
        
        mock_span = Mock()
        mock_par.xhtml_maker.span.return_value = mock_span
        
        result = meta_elt.to_html(mock_par, mock_taxonomy)
        
        mock_taxonomy.get_metadata_by_id.assert_called_once_with("test.name")
        mock_span.append.assert_any_call("fact_element")
        assert result == mock_span
    
    def test_to_html_with_config_value(self):
        """Test HTML generation with config value"""
        mock_data = Mock()
        mock_data.get_config.return_value = "config_value"
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null", mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_taxonomy.get_metadata_by_id.return_value = None
        
        mock_span = Mock()
        mock_par.xhtml_maker.span.return_value = mock_span
        
        result = meta_elt.to_html(mock_par, mock_taxonomy)
        
        mock_data.get_config.assert_called_once_with("test.name", mandatory=False)
        assert result == mock_span
    
    def test_to_html_with_null_value(self):
        """Test HTML generation with null value"""
        mock_data = Mock()
        mock_data.get_config.return_value = None
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null_val", mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_taxonomy.get_metadata_by_id.return_value = None
        
        mock_par.xhtml_maker.span.return_value = "null_span"
        
        result = meta_elt.to_html(mock_par, mock_taxonomy)
        
        assert result == "null_span"
    
    def test_to_text_with_taxonomy_fact(self):
        """Test text generation with taxonomy fact"""
        mock_data = Mock()
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null", mock_data)
        
        mock_taxonomy = Mock()
        mock_fact = Mock()
        mock_fact.value = "fact_value"
        mock_taxonomy.get_metadata_by_id.return_value = mock_fact
        
        out = StringIO()
        meta_elt.to_text(mock_taxonomy, out)
        
        assert out.getvalue() == "prefix:fact_value:suffix"
    
    def test_to_text_with_config_value(self):
        """Test text generation with config value"""
        mock_data = Mock()
        mock_data.get_config.return_value = "config_value"
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null", mock_data)
        
        mock_taxonomy = Mock()
        mock_taxonomy.get_metadata_by_id.return_value = None
        
        out = StringIO()
        meta_elt.to_text(mock_taxonomy, out)
        
        assert out.getvalue() == "prefix:config_value:suffix"
    
    def test_to_text_with_empty_prefixes(self):
        """Test text generation with empty prefixes/suffixes"""
        mock_data = Mock()
        mock_data.get_config.return_value = "config_value"
        meta_elt = MetadataElt("test.name", "", "", "null", mock_data)
        
        mock_taxonomy = Mock()
        mock_taxonomy.get_metadata_by_id.return_value = None
        
        out = StringIO()
        meta_elt.to_text(mock_taxonomy, out)
        
        assert out.getvalue() == "config_value"
    
    def test_to_debug_with_taxonomy_fact(self):
        """Test debug generation with taxonomy fact"""
        mock_data = Mock()
        meta_elt = MetadataElt("test.name", "prefix:", ":suffix", "null", mock_data)
        
        mock_taxonomy = Mock()
        mock_fact = Mock()
        mock_fact.value = "fact_value"
        mock_taxonomy.get_metadata_by_id.return_value = mock_fact
        
        out = StringIO()
        meta_elt.to_debug(mock_taxonomy, out)
        
        assert out.getvalue() == "prefix:fact_value:suffix"


class TestStringElt:
    """Test the StringElt class"""
    
    def test_init(self):
        """Test StringElt initialization"""
        mock_data = Mock()
        str_elt = StringElt("test value", mock_data)
        
        assert str_elt.value == "test value"
        assert str_elt.data == mock_data
    
    def test_load(self):
        """Test loading a string element"""
        mock_data = Mock()
        result = StringElt.load("test value", mock_data)
        
        assert isinstance(result, StringElt)
        assert result.value == "test value"
        assert result.data == mock_data
    
    def test_to_html(self):
        """Test HTML generation"""
        mock_data = Mock()
        str_elt = StringElt("test value", mock_data)
        
        mock_par = Mock()
        mock_par.xhtml_maker.span.return_value = "span_element"
        
        result = str_elt.to_html(mock_par, Mock())
        
        mock_par.xhtml_maker.span.assert_called_once_with("test value")
        assert result == "span_element"
    
    def test_to_text(self):
        """Test text generation"""
        mock_data = Mock()
        str_elt = StringElt("test value", mock_data)
        
        out = StringIO()
        str_elt.to_text(Mock(), out)
        
        assert out.getvalue() == "test value"
    
    def test_to_debug(self):
        """Test debug generation"""
        mock_data = Mock()
        str_elt = StringElt("test value", mock_data)
        
        out = StringIO()
        str_elt.to_debug(Mock(), out)
        
        assert out.getvalue() == "test value"


class TestFactElt:
    """Test the FactElt class"""
    
    def test_init(self):
        """Test FactElt initialization"""
        mock_data = Mock()
        fact_elt = FactElt("test-fact", "test-context", {"attr": "val"}, ["content"], mock_data)
        
        assert fact_elt.fact == "test-fact"
        assert fact_elt.ctxt == "test-context"
        assert fact_elt.attrs == {"attr": "val"}
        assert fact_elt.content == ["content"]
        assert fact_elt.data == mock_data
    
    def test_load_simple_fact(self):
        """Test loading a simple fact"""
        root = {"fact": "test-fact", "context": "test-context"}
        mock_data = Mock()
        
        result = FactElt.load(root, mock_data)
        
        assert isinstance(result, FactElt)
        assert result.fact == "test-fact"
        assert result.ctxt == "test-context"
        assert result.content == []
    
    def test_load_with_string_content(self):
        """Test loading fact with string content"""
        root = {"fact": "test-fact", "content": "test content"}
        mock_data = Mock()
        mock_data.expand_string.return_value = "expanded content"
        
        result = FactElt.load(root, mock_data)
        
        assert len(result.content) == 1
        assert result.content[0] == "expanded content"
    
    def test_load_with_invalid_content_type(self):
        """Test loading fact with invalid content type raises error"""
        root = {"fact": "test-fact", "content": 123}
        mock_data = Mock()
        
        with pytest.raises(RuntimeError, match="Can't handle content being type"):
            FactElt.load(root, mock_data)
    
    def test_to_html_with_default_context(self):
        """Test HTML generation with default context"""
        mock_data = Mock()
        mock_period = Mock()
        mock_business_context = Mock()
        mock_context = Mock()
        mock_data.get_report_period.return_value = mock_period
        mock_data.business_context = mock_business_context
        mock_business_context.with_period.return_value = mock_context
        
        fact_elt = FactElt("test-fact", None, {}, [], mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_fact = Mock() 
        mock_fact.to_elt.return_value = Mock()
        mock_taxonomy.create_fact = Mock(return_value=mock_fact)
        
        with patch('ixbrl_reporter.layout.StringDatum') as mock_datum:
            result = fact_elt.to_html(mock_par, mock_taxonomy)
            
            mock_data.get_report_period.assert_called_once()
            mock_business_context.with_period.assert_called_once_with(mock_period)
            mock_datum.assert_called_once_with("test-fact", [], mock_context)
    
    def test_to_html_with_explicit_context(self):
        """Test HTML generation with explicit context"""
        mock_data = Mock()
        fact_elt = FactElt("test-fact", "explicit-context", {}, [], mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_context = Mock()
        mock_taxonomy.get_context.return_value = mock_context
        mock_fact = Mock()
        mock_fact.to_elt.return_value = Mock()
        mock_taxonomy.create_fact = Mock(return_value=mock_fact)
        
        with patch('ixbrl_reporter.layout.StringDatum') as mock_datum:
            result = fact_elt.to_html(mock_par, mock_taxonomy)
            
            mock_taxonomy.get_context.assert_called_once_with("explicit-context")
            mock_datum.assert_called_once_with("test-fact", [], mock_context)
    
    def test_to_text(self):
        """Test text generation"""
        mock_data = Mock()
        mock_content = Mock()
        fact_elt = FactElt("test-fact", None, {}, [mock_content], mock_data)
        
        out = StringIO()
        fact_elt.to_text(Mock(), out)
        
        mock_content.to_text.assert_called()
    
    def test_to_debug(self):
        """Test debug generation"""
        mock_data = Mock()
        mock_content = Mock()
        fact_elt = FactElt("test-fact", None, {}, [mock_content], mock_data)
        
        out = StringIO()
        fact_elt.to_debug(Mock(), out)
        
        mock_content.to_debug.assert_called()


class TestElementElt:
    """Test the ElementElt class"""
    
    def test_init(self):
        """Test ElementElt initialization"""
        mock_element = Mock()
        mock_data = Mock()
        elem_elt = ElementElt(mock_element, mock_data)
        
        assert elem_elt.elt == mock_element
        assert elem_elt.data == mock_data
    
    def test_load_with_string_element(self):
        """Test loading with string element reference"""
        root = {"element": "test-element"}
        mock_data = Mock()
        mock_element = Mock()
        mock_data.get_element.return_value = mock_element
        
        result = ElementElt.load(root, mock_data)
        
        assert isinstance(result, ElementElt)
        assert result.elt == mock_element
        mock_data.get_element.assert_called_once_with("test-element")
    
    def test_load_with_dict_element(self):
        """Test loading with dict element definition"""
        root = {"element": {"kind": "test", "id": "test-element"}}
        mock_data = Mock()
        mock_element = Mock()
        mock_data.get_element.return_value = mock_element
        
        result = ElementElt.load(root, mock_data)
        
        assert isinstance(result, ElementElt)
        assert result.elt == mock_element
        mock_data.get_element.assert_called_once_with({"kind": "test", "id": "test-element"})
    
    def test_load_with_invalid_element_type(self):
        """Test loading with invalid element type raises error"""
        root = {"element": 123}
        mock_data = Mock()
        
        with pytest.raises(RuntimeError, match="Can't handle element being type"):
            ElementElt.load(root, mock_data)
    
    def test_to_html(self):
        """Test HTML generation"""
        mock_element = Mock()
        mock_element.to_ixbrl_elt.return_value = ["content1", None, "content2"]
        mock_data = Mock()
        elem_elt = ElementElt(mock_element, mock_data)
        
        mock_par = Mock()
        mock_div = Mock()
        mock_par.xhtml_maker.div.return_value = mock_div
        mock_taxonomy = Mock()
        
        result = elem_elt.to_html(mock_par, mock_taxonomy)
        
        mock_element.to_ixbrl_elt.assert_called_once_with(mock_par, mock_taxonomy)
        mock_div.append.assert_any_call("content1")
        mock_div.append.assert_any_call("content2")
        # None content should be skipped
        assert mock_div.append.call_count == 2
        assert result == mock_div
    
    def test_to_text(self):
        """Test text generation"""
        mock_element = Mock()
        mock_data = Mock()
        elem_elt = ElementElt(mock_element, mock_data)
        
        out = StringIO()
        elem_elt.to_text(Mock(), out)
        
        mock_element.to_text.assert_called()
    
    def test_to_debug(self):
        """Test debug generation"""
        mock_element = Mock()
        mock_data = Mock()
        elem_elt = ElementElt(mock_element, mock_data)
        
        out = StringIO()
        elem_elt.to_debug(Mock(), out)
        
        mock_element.to_debug.assert_called()


class TestWorksheetElt:
    """Test the WorksheetElt class"""
    
    def test_init(self):
        """Test WorksheetElt initialization"""
        mock_ws = Mock()
        mock_data = Mock()
        ws_elt = WorksheetElt(mock_ws, mock_data)
        
        assert ws_elt.wse == mock_ws
        assert ws_elt.data == mock_data
    
    def test_load(self):
        """Test loading a worksheet element"""
        root = {"worksheet": "test-worksheet"}
        mock_data = Mock()
        
        with patch('ixbrl_reporter.layout.WorksheetElement.load') as mock_load:
            mock_ws = Mock()
            mock_load.return_value = mock_ws
            
            result = WorksheetElt.load(root, mock_data)
            
            assert isinstance(result, WorksheetElt)
            assert result.wse == mock_ws
            mock_load.assert_called_once_with(root, mock_data)
    
    def test_to_html(self):
        """Test HTML generation"""
        mock_ws = Mock()
        mock_ws.to_ixbrl_elt.return_value = ["worksheet_element"]
        mock_data = Mock()
        ws_elt = WorksheetElt(mock_ws, mock_data)
        
        result = ws_elt.to_html(Mock(), Mock())
        
        assert result == "worksheet_element"
    
    def test_to_text(self):
        """Test text generation"""
        mock_ws = Mock()
        mock_data = Mock()
        ws_elt = WorksheetElt(mock_ws, mock_data)
        
        out = StringIO()
        ws_elt.to_text(Mock(), out)
        
        mock_ws.to_text.assert_called()
    
    def test_to_debug(self):
        """Test debug generation"""
        mock_ws = Mock()
        mock_data = Mock()
        ws_elt = WorksheetElt(mock_ws, mock_data)
        
        out = StringIO()
        ws_elt.to_debug(Mock(), out)
        
        mock_ws.to_debug.assert_called()


class TestComputationElt:
    """Test the ComputationElt class"""
    
    def test_init(self):
        """Test ComputationElt initialization"""
        mock_data = Mock()
        comp_elt = ComputationElt("test-computation", "test-period", mock_data)
        
        assert comp_elt.name == "test-computation"
        assert comp_elt.period == "test-period"
        assert comp_elt.data == mock_data
        assert comp_elt.ctxt is None
    
    def test_to_html_with_default_period(self):
        """Test HTML generation with default period"""
        mock_data = Mock()
        mock_period = Mock()
        mock_data.get_report_period.return_value = mock_period
        mock_result = Mock()
        mock_data.get_result.return_value = mock_result
        mock_context = Mock()
        mock_data.business_context = Mock()
        mock_data.business_context.with_period.return_value = mock_context
        
        comp_elt = ComputationElt("test-computation", "", mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_fact = Mock()
        mock_fact.to_elt.return_value = "fact_element"
        mock_taxonomy.create_fact.return_value = mock_fact
        
        result = comp_elt.to_html(mock_par, mock_taxonomy)
        
        mock_data.get_report_period.assert_called_once_with(0)
        mock_data.get_result.assert_called_once_with("test-computation", mock_period)
        mock_taxonomy.create_fact.assert_called_once_with(mock_result)
        assert result == "fact_element"
    
    def test_to_html_with_named_period(self):
        """Test HTML generation with named period"""
        mock_data = Mock()
        mock_period = Mock()
        mock_data.get_period.return_value = mock_period
        mock_result = Mock()
        mock_data.get_result.return_value = mock_result
        mock_context = Mock()
        mock_data.business_context = Mock()
        mock_data.business_context.with_period.return_value = mock_context
        
        comp_elt = ComputationElt("test-computation", "2020", mock_data)
        
        mock_par = Mock()
        mock_taxonomy = Mock()
        mock_fact = Mock()
        mock_fact.to_elt.return_value = "fact_element"
        mock_taxonomy.create_fact.return_value = mock_fact
        
        result = comp_elt.to_html(mock_par, mock_taxonomy)
        
        mock_data.get_period.assert_called_once_with("2020")
        mock_data.get_result.assert_called_once_with("test-computation", mock_period)
        assert result == "fact_element"
    
    def test_to_text_with_default_period(self):
        """Test text generation with default period"""
        mock_data = Mock()
        mock_period = Mock()
        mock_data.get_report_period.return_value = mock_period
        mock_result = Mock()
        mock_data.get_result.return_value = mock_result
        mock_context = Mock()
        mock_data.business_context = Mock()
        mock_data.business_context.with_period.return_value = mock_context
        
        comp_elt = ComputationElt("test-computation", "", mock_data)
        
        mock_taxonomy = Mock()
        mock_fact = Mock()
        mock_fact.to_text.return_value = "fact_text"
        mock_taxonomy.create_fact.return_value = mock_fact
        
        out = StringIO()
        comp_elt.to_text(mock_taxonomy, out)
        
        mock_data.get_report_period.assert_called_once_with(0)
        mock_data.get_result.assert_called_once_with("test-computation", mock_period)
        mock_fact.to_text.assert_called_once()
    
    def test_to_debug(self):
        """Test debug generation delegates to to_text"""
        mock_data = Mock()
        comp_elt = ComputationElt("test-computation", "", mock_data)
        
        with patch.object(comp_elt, 'to_text') as mock_to_text:
            mock_taxonomy = Mock()
            mock_out = Mock()
            
            comp_elt.to_debug(mock_taxonomy, mock_out)
            
            mock_to_text.assert_called_once_with(mock_taxonomy, mock_out)