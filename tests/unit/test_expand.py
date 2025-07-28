"""
Unit tests for ixbrl_reporter.expand module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from ixbrl_reporter.expand import expand_string
from ixbrl_reporter.note_parse import (
    TextToken, TagOpen, TagClose, MetadataToken, ComputationToken, NoteParser
)
from ixbrl_reporter.layout import (
    StringElt, MetadataElt, ComputationElt, FactElt, TagElt
)


class TestExpandString:
    """Test expand_string function functionality"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
    
    def test_expand_string_template_expansion(self):
        """expand_string should handle template: prefix with recursive expansion"""
        template_value = "This is a template"
        self.mock_data.get_config.return_value = template_value
        
        with patch('ixbrl_reporter.expand.expand_string') as mock_expand:
            # Mock the recursive call
            mock_result = Mock()
            mock_expand.side_effect = [mock_result]  # First call returns result, avoid infinite recursion
            
            result = expand_string("template:my_template", self.mock_data)
            
            # Should look up template config
            self.mock_data.get_config.assert_called_once_with("report.taxonomy.note-templates.my_template")
            
            # Should recursively call expand_string with template content
            mock_expand.assert_called_once_with(template_value, self.mock_data)
            
            assert result == mock_result
    
    def test_expand_string_simple_string_no_prefix(self):
        """expand_string should return StringElt for simple strings without prefix"""
        simple_text = "This is just a simple string"
        
        with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
            mock_string_instance = Mock()
            mock_string_elt.return_value = mock_string_instance
            
            result = expand_string(simple_text, self.mock_data)
            
            # Should create StringElt with the text and data
            mock_string_elt.assert_called_once_with(simple_text, self.mock_data)
            assert result == mock_string_instance
    
    def test_expand_string_expand_prefix_with_text_tokens(self):
        """expand_string should parse expand: content with text tokens"""
        expand_content = "Hello world"
        
        # Mock the parser to return text tokens
        mock_text_token = TextToken("Hello world")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
                with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                    mock_parse.return_value = [mock_text_token]
                    mock_string_instance = Mock()
                    mock_string_elt.return_value = mock_string_instance
                    mock_tag_instance = Mock()
                    mock_tag_elt.return_value = mock_tag_instance
                    
                    result = expand_string(f"expand:{expand_content}", self.mock_data)
                    
                    # Should parse the expand content
                    mock_parse.assert_called_once_with(expand_content)
                    
                    # Should create StringElt for text token
                    mock_string_elt.assert_called_once_with("Hello world", self.mock_data)
                    
                    # Should wrap in TagElt span
                    mock_tag_elt.assert_called_once_with("span", {}, [mock_string_instance], self.mock_data)
                    
                    assert result == mock_tag_instance
    
    def test_expand_string_expand_prefix_with_metadata_tokens(self):
        """expand_string should handle metadata tokens in expand: content"""
        expand_content = "Company: ~{company-name}"
        
        # Mock the parser to return mixed tokens
        mock_text_token = TextToken("Company: ")
        mock_metadata_token = MetadataToken("company-name", "", "", "")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
                with patch('ixbrl_reporter.expand.MetadataElt') as mock_metadata_elt:
                    with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                        mock_parse.return_value = [mock_text_token, mock_metadata_token]
                        mock_string_instance = Mock()
                        mock_metadata_instance = Mock()
                        mock_tag_instance = Mock()
                        mock_string_elt.return_value = mock_string_instance
                        mock_metadata_elt.return_value = mock_metadata_instance
                        mock_tag_elt.return_value = mock_tag_instance
                        
                        result = expand_string(f"expand:{expand_content}", self.mock_data)
                        
                        # Should parse the expand content
                        mock_parse.assert_called_once_with(expand_content)
                        
                        # Should create StringElt for text token
                        mock_string_elt.assert_called_once_with("Company: ", self.mock_data)
                        
                        # Should create MetadataElt for metadata token
                        mock_metadata_elt.assert_called_once_with("company-name", "", "", "", self.mock_data)
                        
                        # Should wrap in TagElt span with both elements
                        mock_tag_elt.assert_called_once_with("span", {}, [mock_string_instance, mock_metadata_instance], self.mock_data)
                        
                        assert result == mock_tag_instance
    
    def test_expand_string_expand_prefix_with_computation_tokens(self):
        """expand_string should handle computation tokens in expand: content"""
        expand_content = "Revenue: #{revenue}"
        
        # Mock the parser to return computation token
        mock_computation_token = ComputationToken("revenue", "context1", "period1")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.ComputationElt') as mock_computation_elt:
                with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                    mock_parse.return_value = [mock_computation_token]
                    mock_computation_instance = Mock()
                    mock_tag_instance = Mock()
                    mock_computation_elt.return_value = mock_computation_instance
                    mock_tag_elt.return_value = mock_tag_instance
                    
                    result = expand_string(f"expand:{expand_content}", self.mock_data)
                    
                    # Should parse the expand content
                    mock_parse.assert_called_once_with(expand_content)
                    
                    # Should create ComputationElt for computation token
                    mock_computation_elt.assert_called_once_with("revenue", "period1", self.mock_data)
                    
                    # Should wrap in TagElt span
                    mock_tag_elt.assert_called_once_with("span", {}, [mock_computation_instance], self.mock_data)
                    
                    assert result == mock_tag_instance
    
    def test_expand_string_expand_prefix_with_string_tags(self):
        """expand_string should handle string tags (TagOpen/TagClose) in expand: content"""
        expand_content = "<fact>content</fact>"
        
        # Mock the parser to return tag tokens
        mock_tag_open = TagOpen("fact", "context1", "string")
        mock_text_token = TextToken("content")
        mock_tag_close = TagClose("fact")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
                with patch('ixbrl_reporter.expand.FactElt') as mock_fact_elt:
                    with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                        mock_parse.return_value = [mock_tag_open, mock_text_token, mock_tag_close]
                        mock_string_instance = Mock()
                        mock_fact_instance = Mock()
                        mock_tag_instance = Mock()
                        mock_string_elt.return_value = mock_string_instance
                        mock_fact_elt.return_value = mock_fact_instance
                        mock_tag_elt.return_value = mock_tag_instance
                        
                        result = expand_string(f"expand:{expand_content}", self.mock_data)
                        
                        # Should parse the expand content
                        mock_parse.assert_called_once_with(expand_content)
                        
                        # Should create StringElt for text content
                        mock_string_elt.assert_called_once_with("content", self.mock_data)
                        
                        # Should create FactElt for the tag
                        mock_fact_elt.assert_called_once_with("fact", "context1", {}, [mock_string_instance], self.mock_data)
                        
                        # Should wrap in TagElt span
                        mock_tag_elt.assert_called_once_with("span", {}, [mock_fact_instance], self.mock_data)
                        
                        assert result == mock_tag_instance
    
    def test_expand_string_expand_prefix_with_nested_tags(self):
        """expand_string should handle nested tags correctly using stack operations"""
        expand_content = "<outer><inner>content</inner></outer>"
        
        # Mock nested tag structure
        mock_outer_open = TagOpen("outer", "ctx1", "string")
        mock_inner_open = TagOpen("inner", "ctx2", "string")
        mock_text_token = TextToken("content")
        mock_inner_close = TagClose("inner")
        mock_outer_close = TagClose("outer")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
                with patch('ixbrl_reporter.expand.FactElt') as mock_fact_elt:
                    with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                        mock_parse.return_value = [mock_outer_open, mock_inner_open, mock_text_token, mock_inner_close, mock_outer_close]
                        mock_string_instance = Mock()
                        mock_inner_fact_instance = Mock()
                        mock_outer_fact_instance = Mock()
                        mock_tag_instance = Mock()
                        
                        mock_string_elt.return_value = mock_string_instance
                        mock_fact_elt.side_effect = [mock_inner_fact_instance, mock_outer_fact_instance]
                        mock_tag_elt.return_value = mock_tag_instance
                        
                        result = expand_string(f"expand:{expand_content}", self.mock_data)
                        
                        # Should parse the expand content
                        mock_parse.assert_called_once_with(expand_content)
                        
                        # Should create StringElt for text content
                        mock_string_elt.assert_called_once_with("content", self.mock_data)
                        
                        # Should create FactElt for both tags (inner first, then outer)
                        assert mock_fact_elt.call_count == 2
                        mock_fact_elt.assert_any_call("inner", "ctx2", {}, [mock_string_instance], self.mock_data)
                        mock_fact_elt.assert_any_call("outer", "ctx1", {}, [mock_inner_fact_instance], self.mock_data)
                        
                        # Should wrap in TagElt span
                        mock_tag_elt.assert_called_once_with("span", {}, [mock_outer_fact_instance], self.mock_data)
                        
                        assert result == mock_tag_instance
    
    def test_expand_string_expand_prefix_non_string_tag_error(self):
        """expand_string should raise error for non-string tag kinds"""
        expand_content = "<fact>content</fact>"
        
        # Mock tag with non-string kind
        mock_tag_open = TagOpen("fact", "context1", "non-string")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            mock_parse.return_value = [mock_tag_open]
            
            with pytest.raises(RuntimeError, match="Only string tags, currently"):
                expand_string(f"expand:{expand_content}", self.mock_data)
    
    def test_expand_string_expand_prefix_mixed_content(self):
        """expand_string should handle mixed content types in expand: strings"""
        expand_content = "Text ~{metadata} #{computation} <fact>tagged</fact> more text"
        
        # Mock mixed token sequence
        mock_text1 = TextToken("Text ")
        mock_metadata = MetadataToken("metadata", "", "", "")
        mock_text2 = TextToken(" ")
        mock_computation = ComputationToken("computation", "", "")
        mock_text3 = TextToken(" ")
        mock_tag_open = TagOpen("fact", "ctx1", "string")
        mock_text4 = TextToken("tagged")
        mock_tag_close = TagClose("fact")
        mock_text5 = TextToken(" more text")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
                with patch('ixbrl_reporter.expand.MetadataElt') as mock_metadata_elt:
                    with patch('ixbrl_reporter.expand.ComputationElt') as mock_computation_elt:
                        with patch('ixbrl_reporter.expand.FactElt') as mock_fact_elt:
                            with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                                mock_parse.return_value = [
                                    mock_text1, mock_metadata, mock_text2, mock_computation, mock_text3,
                                    mock_tag_open, mock_text4, mock_tag_close, mock_text5
                                ]
                                
                                # Set up return values for all mocks  
                                # We have 5 text tokens: "Text ", " ", " ", "tagged", " more text"
                                mock_string_instances = [Mock() for _ in range(5)]  # 5 text elements
                                mock_metadata_instance = Mock()
                                mock_computation_instance = Mock()
                                mock_fact_instance = Mock()
                                mock_tag_instance = Mock()
                                
                                mock_string_elt.side_effect = mock_string_instances
                                mock_metadata_elt.return_value = mock_metadata_instance
                                mock_computation_elt.return_value = mock_computation_instance
                                mock_fact_elt.return_value = mock_fact_instance
                                mock_tag_elt.return_value = mock_tag_instance
                                
                                result = expand_string(f"expand:{expand_content}", self.mock_data)
                                
                                # Should create all elements
                                assert mock_string_elt.call_count == 5
                                mock_metadata_elt.assert_called_once_with("metadata", "", "", "", self.mock_data)
                                mock_computation_elt.assert_called_once_with("computation", "", self.mock_data)
                                mock_fact_elt.assert_called_once_with("fact", "ctx1", {}, [mock_string_instances[3]], self.mock_data)
                                
                                # Check that TagElt was called with span and data
                                mock_tag_elt.assert_called_once()
                                call_args = mock_tag_elt.call_args
                                assert call_args[0][0] == "span"  # tag
                                assert call_args[0][1] == {}      # attrs
                                assert call_args[0][3] == self.mock_data  # data
                                
                                assert result == mock_tag_instance
    
    def test_expand_string_template_with_complex_expansion(self):
        """expand_string should handle template that contains expand: content"""
        template_content = "expand:Hello ~{name}"
        self.mock_data.get_config.return_value = template_content
        
        # Mock the recursive expansion
        mock_text_token = TextToken("Hello ")
        mock_metadata_token = MetadataToken("name", "", "", "")
        
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
                with patch('ixbrl_reporter.expand.MetadataElt') as mock_metadata_elt:
                    with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                        mock_parse.return_value = [mock_text_token, mock_metadata_token]
                        mock_string_instance = Mock()
                        mock_metadata_instance = Mock()
                        mock_tag_instance = Mock()
                        
                        mock_string_elt.return_value = mock_string_instance
                        mock_metadata_elt.return_value = mock_metadata_instance
                        mock_tag_elt.return_value = mock_tag_instance
                        
                        # This will trigger the actual recursive call
                        result = expand_string("template:greeting", self.mock_data)
                        
                        # Should look up template
                        self.mock_data.get_config.assert_called_once_with("report.taxonomy.note-templates.greeting")
                        
                        # Should process the expand: content from template
                        mock_parse.assert_called_once_with("Hello ~{name}")
                        
                        assert result == mock_tag_instance
    
    def test_expand_string_empty_expand_content(self):
        """expand_string should handle empty expand: content"""
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                mock_parse.return_value = []  # Empty token list
                mock_tag_instance = Mock()
                mock_tag_elt.return_value = mock_tag_instance
                
                result = expand_string("expand:", self.mock_data)
                
                # Should parse empty content
                mock_parse.assert_called_once_with("")
                
                # Should create empty span
                mock_tag_elt.assert_called_once_with("span", {}, [], self.mock_data)
                
                assert result == mock_tag_instance


class TestExpandStringIntegration:
    """Integration tests for expand_string with real dependencies"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
    
    def test_expand_string_with_real_note_parser(self):
        """Integration test using real NoteParser with simple text"""
        simple_text = "Hello World"
        
        with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
            with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                mock_string_instance = Mock()
                mock_tag_instance = Mock()
                mock_string_elt.return_value = mock_string_instance
                mock_tag_elt.return_value = mock_tag_instance
                
                result = expand_string(f"expand:{simple_text}", self.mock_data)
                
                # Should create StringElt for the text
                mock_string_elt.assert_called_once_with(simple_text, self.mock_data)
                
                # Should wrap in TagElt span
                mock_tag_elt.assert_called_once_with("span", {}, [mock_string_instance], self.mock_data)
                
                assert result == mock_tag_instance
    
    def test_expand_string_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with just "expand:" prefix and nothing else
        with patch('ixbrl_reporter.expand.NoteParser.parse') as mock_parse:
            with patch('ixbrl_reporter.expand.TagElt') as mock_tag_elt:
                mock_parse.return_value = []
                mock_tag_instance = Mock()
                mock_tag_elt.return_value = mock_tag_instance
                
                result = expand_string("expand:", self.mock_data)
                
                mock_parse.assert_called_once_with("")
                mock_tag_elt.assert_called_once_with("span", {}, [], self.mock_data)
                assert result == mock_tag_instance
        
        # Test with just "template:" prefix and nothing else
        self.mock_data.get_config.return_value = "simple text"
        
        with patch('ixbrl_reporter.expand.StringElt') as mock_string_elt:
            mock_string_instance = Mock()
            mock_string_elt.return_value = mock_string_instance
            
            result = expand_string("template:", self.mock_data)
            
            self.mock_data.get_config.assert_called_with("report.taxonomy.note-templates.")
            mock_string_elt.assert_called_once_with("simple text", self.mock_data)
            assert result == mock_string_instance