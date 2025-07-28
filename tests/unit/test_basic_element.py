"""
Unit tests for ixbrl_reporter.basic_element module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO
from lxml import objectify, etree

from ixbrl_reporter.basic_element import BasicElement


class TestBasicElementInit:
    """Test BasicElement initialization"""
    
    def test_basic_element_creation_with_id(self):
        """BasicElement should initialize with provided id"""
        mock_data = Mock()
        element = BasicElement("test-id", mock_data)
        
        assert element.id == "test-id"
        assert element.data == mock_data
    
    def test_basic_element_creation_without_id(self):
        """BasicElement should generate UUID when id is None"""
        mock_data = Mock()
        
        with patch('ixbrl_reporter.basic_element.create_uuid', return_value="abc123"):
            element = BasicElement(None, mock_data)
        
        assert element.id == "elt-abc123"
        assert element.data == mock_data
    
    def test_basic_element_creation_with_empty_id(self):
        """BasicElement should generate UUID when id is empty string"""
        mock_data = Mock()
        
        with patch('ixbrl_reporter.basic_element.create_uuid', return_value="def456"):
            element = BasicElement("", mock_data)
        
        assert element.id == "elt-def456"
        assert element.data == mock_data
    
    def test_basic_element_creation_with_falsy_id(self):
        """BasicElement should generate UUID for any falsy id"""
        mock_data = Mock()
        falsy_values = [None, "", 0, False, []]
        
        for falsy_id in falsy_values:
            with patch('ixbrl_reporter.basic_element.create_uuid', return_value="test123"):
                element = BasicElement(falsy_id, mock_data)
                assert element.id == "elt-test123"


class TestBasicElementAddMakers:
    """Test BasicElement.add_makers method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
    
    def test_add_makers_creates_all_makers(self):
        """add_makers should create all required element makers"""
        nsmap = {"test": "http://test.namespace"}
        
        with patch('ixbrl_reporter.basic_element.objectify.ElementMaker') as mock_maker_class:
            mock_maker = Mock()
            mock_maker_class.return_value = mock_maker
            
            self.element.add_makers(nsmap)
        
        # Should create 5 different makers
        assert mock_maker_class.call_count == 5
        
        # Verify all makers are set
        assert self.element.xhtml_maker == mock_maker
        assert self.element.ix_maker == mock_maker
        assert self.element.xlink_maker == mock_maker
        assert self.element.link_maker == mock_maker
        assert self.element.xbrli_maker == mock_maker
        assert self.element.xbrldi_maker == mock_maker
    
    def test_add_makers_namespaces(self):
        """add_makers should use correct namespaces"""
        nsmap = {"custom": "http://custom.namespace"}
        
        with patch('ixbrl_reporter.basic_element.objectify.ElementMaker') as mock_maker_class:
            self.element.add_makers(nsmap)
        
        # Check namespace arguments
        calls = mock_maker_class.call_args_list
        
        # XHTML maker should include nsmap
        xhtml_call = calls[0]
        assert xhtml_call[1]['nsmap'] == nsmap
        assert xhtml_call[1]['namespace'] == "http://www.w3.org/1999/xhtml"
        
        # IX maker
        ix_call = calls[1]
        assert ix_call[1]['namespace'] == "http://www.xbrl.org/2013/inlineXBRL"
    
    def test_add_makers_annotate_false(self):
        """add_makers should set annotate=False for all makers"""
        nsmap = {}
        
        with patch('ixbrl_reporter.basic_element.objectify.ElementMaker') as mock_maker_class:
            self.element.add_makers(nsmap)
        
        # All calls should have annotate=False
        for call_args in mock_maker_class.call_args_list:
            assert call_args[1]['annotate'] is False


class TestBasicElementInitHtml:
    """Test BasicElement.init_html method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        self.mock_taxonomy = Mock()
    
    def test_init_html_creates_nsmap(self):
        """init_html should create namespace map with defaults"""
        self.mock_taxonomy.get_namespaces.return_value = {"custom": "http://custom.ns"}
        
        with patch.object(self.element, 'add_makers') as mock_add_makers:
            self.element.init_html(self.mock_taxonomy)
        
        # Check nsmap contains defaults
        expected_keys = [None, "ix", "link", "xlink", "xbrli", "xbrldi", "ixt2", "iso4217", "custom"]
        for key in expected_keys:
            assert key in self.element.nsmap
        
        # Verify add_makers was called with nsmap
        mock_add_makers.assert_called_once_with(self.element.nsmap)
    
    def test_init_html_merges_taxonomy_namespaces(self):
        """init_html should merge taxonomy namespaces into nsmap"""
        taxonomy_ns = {
            "ukgaap": "http://www.xbrl.org/uk/gaap/core/2009-09-01",
            "test": "http://test.namespace"
        }
        self.mock_taxonomy.get_namespaces.return_value = taxonomy_ns
        
        with patch.object(self.element, 'add_makers'):
            self.element.init_html(self.mock_taxonomy)
        
        # Custom namespaces should be in nsmap
        assert self.element.nsmap["ukgaap"] == "http://www.xbrl.org/uk/gaap/core/2009-09-01"
        assert self.element.nsmap["test"] == "http://test.namespace"
    
    def test_init_html_default_namespaces(self):
        """init_html should include all default namespaces"""
        self.mock_taxonomy.get_namespaces.return_value = {}
        
        with patch.object(self.element, 'add_makers'):
            self.element.init_html(self.mock_taxonomy)
        
        # Check all default namespaces are present
        expected_defaults = {
            None: "http://www.w3.org/1999/xhtml",
            "ix": "http://www.xbrl.org/2013/inlineXBRL",
            "link": "http://www.xbrl.org/2003/linkbase",
            "xlink": "http://www.w3.org/1999/xlink",
            "xbrli": "http://www.xbrl.org/2003/instance",
            "xbrldi": "http://xbrl.org/2006/xbrldi",
            "ixt2": "http://www.xbrl.org/inlineXBRL/transformation/2011-07-31",
            "iso4217": "http://www.xbrl.org/2003/iso4217"
        }
        
        for key, value in expected_defaults.items():
            assert self.element.nsmap[key] == value


class TestBasicElementAddStyle:
    """Test BasicElement.add_style method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        
        # Mock xhtml_maker
        self.mock_style_element = Mock()
        self.element.xhtml_maker = Mock()
        self.element.xhtml_maker.style.return_value = self.mock_style_element
    
    def test_add_style_basic_functionality(self):
        """add_style should create and append style element"""
        mock_element = Mock()
        style_text = "body { color: red; }"
        self.mock_data.get_config.return_value = style_text
        
        self.element.add_style(mock_element)
        
        # Verify config was retrieved
        self.mock_data.get_config.assert_called_once_with("report.style")
        
        # Verify style element was created and configured
        self.element.xhtml_maker.style.assert_called_once_with(style_text)
        self.mock_style_element.set.assert_called_once_with("type", "text/css")
        
        # Verify style was appended to element
        mock_element.append.assert_called_once_with(self.mock_style_element)
    
    def test_add_style_with_empty_style(self):
        """add_style should handle empty style text"""
        mock_element = Mock()
        self.mock_data.get_config.return_value = ""
        
        self.element.add_style(mock_element)
        
        # Should still create style element even with empty content
        self.element.xhtml_maker.style.assert_called_once_with("")
        mock_element.append.assert_called_once_with(self.mock_style_element)
    
    def test_add_style_with_complex_css(self):
        """add_style should handle complex CSS"""
        mock_element = Mock()
        complex_css = """
        body { font-family: Arial; }
        .report { margin: 10px; }
        .fact { color: blue; }
        """
        self.mock_data.get_config.return_value = complex_css
        
        self.element.add_style(mock_element)
        
        self.element.xhtml_maker.style.assert_called_once_with(complex_css)
        mock_element.append.assert_called_once_with(self.mock_style_element)


class TestBasicElementContextCreation:
    """Test BasicElement context creation methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        
        # Mock xbrli_maker
        self.element.xbrli_maker = Mock()
    
    def test_create_context_basic(self):
        """create_context should create context with id and elements"""
        mock_context = Mock()
        self.element.xbrli_maker.context.return_value = mock_context
        
        mock_elts = [Mock(), Mock()]
        result = self.element.create_context("test-context", mock_elts)
        
        # Verify context creation
        self.element.xbrli_maker.context.assert_called_once_with({"id": "test-context"})
        
        # Verify elements were appended
        for elt in mock_elts:
            mock_context.append.assert_any_call(elt)
        
        assert result == mock_context
    
    def test_create_context_empty_elements(self):
        """create_context should handle empty elements list"""
        mock_context = Mock()
        self.element.xbrli_maker.context.return_value = mock_context
        
        result = self.element.create_context("empty-context", [])
        
        self.element.xbrli_maker.context.assert_called_once_with({"id": "empty-context"})
        mock_context.append.assert_not_called()
        assert result == mock_context
    
    def test_create_entity_basic(self):
        """create_entity should create entity with identifier"""
        mock_entity = Mock()
        mock_identifier = Mock()
        self.element.xbrli_maker.entity.return_value = mock_entity
        self.element.xbrli_maker.identifier.return_value = mock_identifier
        
        result = self.element.create_entity("entity-123", "http://scheme.test")
        
        # Verify identifier creation
        self.element.xbrli_maker.identifier.assert_called_once_with(
            {"scheme": "http://scheme.test"}, "entity-123"
        )
        
        # Verify entity creation
        self.element.xbrli_maker.entity.assert_called_once_with(mock_identifier)
        
        assert result == mock_entity
    
    def test_create_entity_with_segments(self):
        """create_entity should handle additional segment elements"""
        mock_entity = Mock()
        mock_identifier = Mock()
        self.element.xbrli_maker.entity.return_value = mock_entity
        self.element.xbrli_maker.identifier.return_value = mock_identifier
        
        mock_segments = [Mock(), Mock()]
        result = self.element.create_entity("entity-123", "http://scheme.test", mock_segments)
        
        # Verify segments were appended
        for segment in mock_segments:
            mock_entity.append.assert_any_call(segment)
    
    def test_create_entity_none_elements(self):
        """create_entity should handle None elements parameter"""
        mock_entity = Mock()
        mock_identifier = Mock()
        self.element.xbrli_maker.entity.return_value = mock_entity
        self.element.xbrli_maker.identifier.return_value = mock_identifier
        
        result = self.element.create_entity("entity-123", "http://scheme.test", None)
        
        # Should not crash, should not append anything
        mock_entity.append.assert_not_called()
        assert result == mock_entity
    
    def test_create_instant(self):
        """create_instant should create period with instant date"""
        mock_period = Mock()
        mock_instant = Mock()
        self.element.xbrli_maker.period.return_value = mock_period
        self.element.xbrli_maker.instant.return_value = mock_instant
        
        from datetime import date
        test_date = date(2023, 12, 31)
        
        result = self.element.create_instant(test_date)
        
        # Verify instant creation
        self.element.xbrli_maker.instant.assert_called_once_with("2023-12-31")
        self.element.xbrli_maker.period.assert_called_once_with(mock_instant)
        
        assert result == mock_period
    
    def test_create_period(self):
        """create_period should create period with start and end dates"""
        mock_period = Mock()
        mock_start = Mock()
        mock_end = Mock()
        self.element.xbrli_maker.period.return_value = mock_period
        self.element.xbrli_maker.startDate.return_value = mock_start
        self.element.xbrli_maker.endDate.return_value = mock_end
        
        from datetime import date
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        result = self.element.create_period(start_date, end_date)
        
        # Verify date creation
        self.element.xbrli_maker.startDate.assert_called_once_with("2023-01-01")
        self.element.xbrli_maker.endDate.assert_called_once_with("2023-12-31")
        self.element.xbrli_maker.period.assert_called_once_with(mock_start, mock_end)
        
        assert result == mock_period
    
    def test_create_segment_member(self):
        """create_segment_member should create explicit member with dimension"""
        mock_member = Mock()
        self.element.xbrli_maker.explicitMember.return_value = mock_member
        
        result = self.element.create_segment_member("test:Dimension", "test:Member")
        
        # Verify member creation
        self.element.xbrli_maker.explicitMember.assert_called_once_with("test:Member")
        mock_member.set.assert_called_once_with("dimension", "test:Dimension")
        
        assert result == mock_member


class TestBasicElementToIxbrl:
    """Test BasicElement.to_ixbrl method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        self.mock_taxonomy = Mock()
        self.output = StringIO()
    
    def test_to_ixbrl_basic_workflow(self):
        """to_ixbrl should generate iXBRL document and write to output"""
        mock_tree = Mock()
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html>test</html>'
                
                # Configure pretty-print to False
                self.mock_data.get_config_bool.return_value = False
                
                self.element.to_ixbrl(self.mock_taxonomy, self.output)
        
        # Verify tree generation
        self.element.to_ixbrl_tree.assert_called_once_with(self.mock_taxonomy)
        
        # Verify pretty-print config check
        self.mock_data.get_config_bool.assert_called_once_with("pretty-print", mandatory=False)
        
        # Verify serialization
        mock_tostring.assert_called_once_with(mock_tree, xml_declaration=True)
        
        # Check output
        assert self.output.getvalue() == '<html>test</html>'
    
    def test_to_ixbrl_pretty_print_enabled(self):
        """to_ixbrl should use pretty printing when enabled"""
        mock_tree = Mock()
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html>\n  <body>test</body>\n</html>'
                
                # Configure pretty-print to True
                self.mock_data.get_config_bool.return_value = True
                
                self.element.to_ixbrl(self.mock_taxonomy, self.output)
        
        # Verify pretty printing was used
        mock_tostring.assert_called_once_with(
            mock_tree, pretty_print=True, xml_declaration=True
        )
        
        assert self.output.getvalue() == '<html>\n  <body>test</body>\n</html>'
    
    def test_to_ixbrl_return_value(self):
        """to_ixbrl should return None"""
        mock_tree = Mock()
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html>test</html>'
                self.mock_data.get_config_bool.return_value = False
                
                result = self.element.to_ixbrl(self.mock_taxonomy, self.output)
        
        assert result is None


class TestBasicElementToHtml:
    """Test BasicElement.to_html method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        self.mock_taxonomy = Mock()
        self.output = StringIO()
        
        # Mock xhtml_maker
        self.element.xhtml_maker = Mock()
    
    def test_to_html_ix_element_conversion(self):
        """to_html should convert ix: elements to span elements"""
        # Create a mock iXBRL tree
        mock_ixbrl_tree = Mock()
        
        # Mock the element's attributes for ix namespace conversion
        mock_ixbrl_tree.nsmap = {None: "http://www.xbrl.org/2013/inlineXBRL"}
        mock_ixbrl_tree.prefix = None
        mock_ixbrl_tree.tag = "{http://www.xbrl.org/2013/inlineXBRL}nonfraction"
        mock_ixbrl_tree.text = "1000"
        mock_ixbrl_tree.iterchildren.return_value = []
        
        # Mock span creation
        mock_span = Mock()
        self.element.xhtml_maker.span.return_value = mock_span
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_ixbrl_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html>converted</html>'
                self.mock_data.get_config_bool.return_value = False
                
                self.element.to_html(self.mock_taxonomy, self.output)
        
        # Should have created span for ix element
        self.element.xhtml_maker.span.assert_called()
    
    def test_to_html_header_conversion(self):
        """to_html should convert ix:header to empty span"""
        mock_ixbrl_tree = Mock()
        mock_ixbrl_tree.nsmap = {None: "http://www.xbrl.org/2013/inlineXBRL"}
        mock_ixbrl_tree.prefix = None
        mock_ixbrl_tree.tag = "{http://www.xbrl.org/2013/inlineXBRL}header"
        mock_ixbrl_tree.iterchildren.return_value = []
        
        mock_empty_span = Mock()
        self.element.xhtml_maker.span.return_value = mock_empty_span
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_ixbrl_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html>converted</html>'
                self.mock_data.get_config_bool.return_value = False
                
                self.element.to_html(self.mock_taxonomy, self.output)
        
        # Should create empty span for header
        self.element.xhtml_maker.span.assert_called_with("")
    
    def test_to_html_pretty_print(self):
        """to_html should respect pretty-print configuration"""
        mock_tree = Mock()
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_tree):
            # Mock the walk function by patching it
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html>\n  <body/>\n</html>'
                self.mock_data.get_config_bool.return_value = True
                
                # Mock the walk function result
                mock_converted_tree = Mock()
                with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_converted_tree):
                    # Set up basic attributes to prevent AttributeError
                    mock_converted_tree.nsmap = {"test": "http://test.ns"}
                    mock_converted_tree.prefix = "test"
                    mock_converted_tree.tag = "html"
                    mock_converted_tree.text = None
                    mock_converted_tree.keys.return_value = []
                    mock_converted_tree.iterchildren.return_value = []
                    
                    self.element.to_html(self.mock_taxonomy, self.output)
        
        # Should use pretty printing
        assert mock_tostring.call_args[1]['pretty_print'] is True


class TestBasicElementToIxbrlTree:
    """Test BasicElement.to_ixbrl_tree method - the core iXBRL generation"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        self.mock_taxonomy = Mock()
        
        # Mock all the maker objects
        self.mock_xhtml_maker = Mock()
        self.mock_ix_maker = Mock()
        self.mock_link_maker = Mock()
        
        # Set up config value for title
        mock_title_config = Mock()
        self.mock_data.get_config.return_value = mock_title_config
        self.mock_data.get_config.side_effect = lambda key: {
            "report.title": mock_title_config,
            "metadata.accounting.currency": "GBP",
            "report.style": "body { color: black; }"
        }.get(key, Mock())
    
    def test_to_ixbrl_tree_basic_structure(self):
        """to_ixbrl_tree should create basic HTML structure"""
        # Mock the components
        mock_html = Mock()
        mock_head = Mock()
        mock_body = Mock()
        mock_div = Mock()
        mock_header = Mock()
        
        self.mock_xhtml_maker.html.return_value = mock_html
        self.mock_xhtml_maker.head.return_value = mock_head
        self.mock_xhtml_maker.body.return_value = mock_body
        self.mock_xhtml_maker.div.return_value = mock_div
        self.mock_ix_maker.header.return_value = mock_header
        
        # Mock taxonomy methods
        self.mock_taxonomy.get_namespaces.return_value = {}
        self.mock_taxonomy.get_schemas.return_value = []
        self.mock_taxonomy.get_document_metadata.return_value = []
        self.mock_taxonomy.contexts = {}
        
        with patch.object(self.element, 'init_html'):
            with patch.object(self.element, 'add_style'):
                with patch.object(self.element, 'create_metadata'):
                    with patch.object(self.element, 'create_contexts'):
                        with patch.object(self.element, 'to_ixbrl_elt', return_value=[]):
                            # Set makers manually since init_html is mocked
                            self.element.xhtml_maker = self.mock_xhtml_maker
                            self.element.ix_maker = self.mock_ix_maker
                            self.element.link_maker = self.mock_link_maker
                            self.element.xbrli_maker = Mock()
                            
                            result = self.element.to_ixbrl_tree(self.mock_taxonomy)
        
        # Verify HTML structure creation
        self.mock_xhtml_maker.html.assert_called_once()
        self.mock_xhtml_maker.head.assert_called_once()
        self.mock_xhtml_maker.body.assert_called_once()
        
        assert result == mock_html
    
    def test_to_ixbrl_tree_title_handling(self):
        """to_ixbrl_tree should handle title configuration"""
        mock_html = Mock()
        mock_head = Mock()
        mock_title_element = Mock()
        
        # Set up HTML structure
        mock_html.head = mock_head
        self.mock_xhtml_maker.html.return_value = mock_html
        self.mock_xhtml_maker.title.return_value = mock_title_element
        
        # Mock title config that has a 'use' method
        mock_title_config = Mock()
        self.mock_data.get_config.return_value = mock_title_config
        
        # Mock other required components
        self.mock_taxonomy.get_namespaces.return_value = {}
        self.mock_taxonomy.get_schemas.return_value = []
        self.mock_taxonomy.get_document_metadata.return_value = []
        self.mock_taxonomy.contexts = {}
        
        with patch.object(self.element, 'init_html'):
            with patch.object(self.element, 'add_style'):
                with patch.object(self.element, 'create_metadata'):
                    with patch.object(self.element, 'create_contexts'):
                        with patch.object(self.element, 'to_ixbrl_elt', return_value=[]):
                            self.element.xhtml_maker = self.mock_xhtml_maker
                            self.element.ix_maker = Mock()
                            self.element.link_maker = Mock()
                            self.element.xbrli_maker = Mock()
                            
                            self.element.to_ixbrl_tree(self.mock_taxonomy)
        
        # Verify title config was accessed and used
        self.mock_data.get_config.assert_any_call("report.title")
        mock_title_config.use.assert_called_once()
    
    def test_to_ixbrl_tree_schema_references(self):
        """to_ixbrl_tree should add schema references from taxonomy"""
        mock_schemas = [
            "http://www.xbrl.org/uk/fr/gcd/2004-12-01.xsd",
            "http://www.xbrl.org/uk/gaap/core/2009-09-01.xsd"
        ]
        self.mock_taxonomy.get_schemas.return_value = mock_schemas
        self.mock_taxonomy.get_namespaces.return_value = {}
        self.mock_taxonomy.get_document_metadata.return_value = []
        self.mock_taxonomy.contexts = {}
        
        # Mock schema references
        mock_schema_refs = [Mock(), Mock()]
        self.mock_link_maker.schemaRef.side_effect = mock_schema_refs
        
        # Mock header structure
        mock_header = Mock()
        mock_references = Mock()
        mock_header.references = mock_references
        
        with patch.object(self.element, 'init_html'):
            with patch.object(self.element, 'add_style'):
                with patch.object(self.element, 'create_metadata'):
                    with patch.object(self.element, 'create_contexts'):
                        with patch.object(self.element, 'to_ixbrl_elt', return_value=[]):
                            with patch('ixbrl_reporter.basic_element.objectify.ObjectPath') as mock_path:
                                mock_path.return_value.return_value = mock_header
                                
                                self.element.xhtml_maker = Mock()
                                self.element.ix_maker = Mock()
                                self.element.link_maker = self.mock_link_maker
                                self.element.xbrli_maker = Mock()
                                
                                self.element.to_ixbrl_tree(self.mock_taxonomy)
        
        # Verify schema references were created and added
        assert self.mock_link_maker.schemaRef.call_count == 2
        for i, schema_ref in enumerate(mock_schema_refs):
            schema_ref.set.assert_any_call("{http://www.w3.org/1999/xlink}type", "simple")
            schema_ref.set.assert_any_call("{http://www.w3.org/1999/xlink}href", mock_schemas[i])
            mock_references.append.assert_any_call(schema_ref)
    
    def test_to_ixbrl_tree_currency_units(self):
        """to_ixbrl_tree should create currency and pure units"""
        self.mock_taxonomy.get_namespaces.return_value = {}
        self.mock_taxonomy.get_schemas.return_value = []
        self.mock_taxonomy.get_document_metadata.return_value = []
        self.mock_taxonomy.contexts = {}
        
        # Mock currency config
        self.mock_data.get_config.side_effect = lambda key: {
            "metadata.accounting.currency": "USD",
            "report.title": Mock(),
            "report.style": ""
        }[key]
        
        # Mock unit creation
        mock_currency_unit = Mock()
        mock_pure_unit = Mock()
        mock_currency_measure = Mock()
        mock_pure_measure = Mock()
        
        mock_xbrli_maker = Mock()
        mock_xbrli_maker.unit.side_effect = [mock_currency_unit, mock_pure_unit]
        mock_xbrli_maker.measure.side_effect = [mock_currency_measure, mock_pure_measure]
        
        # Mock header structure
        mock_header = Mock()
        mock_resources = Mock()
        mock_header.resources = mock_resources
        
        with patch.object(self.element, 'init_html'):
            with patch.object(self.element, 'add_style'):
                with patch.object(self.element, 'create_metadata'):
                    with patch.object(self.element, 'create_contexts'):
                        with patch.object(self.element, 'to_ixbrl_elt', return_value=[]):
                            with patch('ixbrl_reporter.basic_element.objectify.ObjectPath') as mock_path:
                                mock_path.return_value.return_value = mock_header
                                
                                self.element.xhtml_maker = Mock()
                                self.element.ix_maker = Mock()
                                self.element.link_maker = Mock()  
                                self.element.xbrli_maker = mock_xbrli_maker
                                
                                self.element.to_ixbrl_tree(self.mock_taxonomy)
        
        # Verify currency unit creation
        mock_xbrli_maker.measure.assert_any_call("iso4217:USD")
        mock_xbrli_maker.unit.assert_any_call({"id": "USD"}, mock_currency_measure)
        mock_resources.append.assert_any_call(mock_currency_unit)
        
        # Verify pure unit creation
        mock_xbrli_maker.measure.assert_any_call("xbrli:pure")
        mock_xbrli_maker.unit.assert_any_call({"id": "pure"}, mock_pure_measure)
        mock_resources.append.assert_any_call(mock_pure_unit)


class TestBasicElementCreateContexts:
    """Test BasicElement.create_contexts method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        self.mock_taxonomy = Mock()
        
        # Mock header and resources
        self.mock_header = Mock()
        self.mock_resources = Mock()
        self.mock_header.resources = self.mock_resources
        self.element.header = self.mock_header
        
        # Mock xbrli_maker
        self.element.xbrli_maker = Mock()
    
    def test_create_contexts_skips_unused_contexts(self):
        """create_contexts should skip contexts not in contexts_used"""
        mock_context1 = Mock()
        mock_context2 = Mock()
        
        # Set up contexts - only context1 is used
        self.mock_taxonomy.contexts = {
            mock_context1: "ctx1",
            mock_context2: "ctx2"
        }
        self.mock_taxonomy.contexts_used = {"ctx1"}  # Only ctx1 is used
        
        with patch.object(self.element, 'create_context') as mock_create:
            self.element.create_contexts(self.mock_taxonomy)
        
        # Should only create one context
        mock_create.assert_called_once()
    
    def test_create_contexts_entity_dimension(self):
        """create_contexts should handle entity dimensions"""
        mock_context = Mock()
        mock_context.get_dimensions.return_value = [
            ("entity", "http://test.scheme", "entity-123")
        ]
        
        self.mock_taxonomy.contexts = {mock_context: "ctx1"}
        self.mock_taxonomy.contexts_used = {"ctx1"}
        
        mock_entity = Mock()
        with patch.object(self.element, 'create_entity', return_value=mock_entity) as mock_create_entity:
            with patch.object(self.element, 'create_context', return_value=Mock()) as mock_create_context:
                self.element.create_contexts(self.mock_taxonomy)
        
        # Verify entity creation
        mock_create_entity.assert_called_once_with("entity-123", "http://test.scheme", [])
        mock_create_context.assert_called_once_with("ctx1", [mock_entity])
    
    def test_create_contexts_period_dimension(self):
        """create_contexts should handle period dimensions"""
        from datetime import date
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        mock_context = Mock()
        mock_context.get_dimensions.return_value = [
            ("period", start_date, end_date)
        ]
        
        self.mock_taxonomy.contexts = {mock_context: "ctx1"}
        self.mock_taxonomy.contexts_used = {"ctx1"}
        
        mock_period = Mock()
        with patch.object(self.element, 'create_period', return_value=mock_period) as mock_create_period:
            with patch.object(self.element, 'create_context', return_value=Mock()) as mock_create_context:
                self.element.create_contexts(self.mock_taxonomy)
        
        # Verify period creation
        mock_create_period.assert_called_once_with(start_date, end_date)
        mock_create_context.assert_called_once_with("ctx1", [mock_period])
    
    def test_create_contexts_instant_dimension(self):
        """create_contexts should handle instant dimensions"""
        from datetime import date
        instant_date = date(2023, 12, 31)
        
        mock_context = Mock()
        mock_context.get_dimensions.return_value = [
            ("instant", instant_date)
        ]
        
        self.mock_taxonomy.contexts = {mock_context: "ctx1"}
        self.mock_taxonomy.contexts_used = {"ctx1"}
        
        mock_instant = Mock()
        with patch.object(self.element, 'create_instant', return_value=mock_instant) as mock_create_instant:
            with patch.object(self.element, 'create_context', return_value=Mock()) as mock_create_context:
                self.element.create_contexts(self.mock_taxonomy)
        
        # Verify instant creation
        mock_create_instant.assert_called_once_with(instant_date)
        mock_create_context.assert_called_once_with("ctx1", [mock_instant])
    
    def test_create_contexts_segment_dimensions(self):
        """create_contexts should handle segment dimensions"""
        mock_context = Mock()
        mock_context.get_dimensions.return_value = [
            ("entity", "http://scheme.test", "entity-123"),
            ("segment", "test:Dimension", "test:Member")
        ]
        
        self.mock_taxonomy.contexts = {mock_context: "ctx1"}
        self.mock_taxonomy.contexts_used = {"ctx1"}
        
        # Mock segment handling
        mock_dimension = Mock()
        mock_segment_desc = Mock()
        mock_dimension.describe.return_value = mock_segment_desc
        self.mock_taxonomy.lookup_dimension.return_value = mock_dimension
        
        mock_segment = Mock()
        self.element.xbrli_maker.segment.return_value = mock_segment
        
        mock_entity = Mock()
        with patch.object(self.element, 'create_entity', return_value=mock_entity) as mock_create_entity:
            with patch.object(self.element, 'create_context', return_value=Mock()):
                self.element.create_contexts(self.mock_taxonomy)
        
        # Verify segment processing
        self.mock_taxonomy.lookup_dimension.assert_called_once_with("test:Dimension", "test:Member")
        mock_dimension.describe.assert_called_once_with(self.element)
        mock_segment.append.assert_called_once_with(mock_segment_desc)
        
        # Verify entity was created with segments
        mock_create_entity.assert_called_once_with("entity-123", "http://scheme.test", [mock_segment])
    
    def test_create_contexts_unknown_dimension_raises_error(self):
        """create_contexts should raise error for unknown dimension types"""
        mock_context = Mock()
        mock_context.get_dimensions.return_value = [
            ("unknown", "some", "data")
        ]
        
        self.mock_taxonomy.contexts = {mock_context: "ctx1"}
        self.mock_taxonomy.contexts_used = {"ctx1"}
        
        with pytest.raises(RuntimeError, match="Should not happen in create_contexts"):
            self.element.create_contexts(self.mock_taxonomy)


class TestBasicElementCreateMetadata:
    """Test BasicElement.create_metadata method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("test", self.mock_data)
        self.mock_taxonomy = Mock()
        self.mock_maker = Mock()
        
        # Mock header structure
        self.mock_header = Mock()
        self.mock_hidden = Mock()
        self.mock_header.hidden = self.mock_hidden
        self.element.header = self.mock_header
    
    def test_create_metadata_with_named_facts(self):
        """create_metadata should add facts with names to hidden section"""
        # Mock facts with names
        mock_fact1 = Mock()
        mock_fact1.name = "test:EntityName"
        mock_fact1_elt = Mock()
        mock_fact1.to_elt.return_value = mock_fact1_elt
        
        mock_fact2 = Mock()
        mock_fact2.name = "test:ReportDate"
        mock_fact2_elt = Mock()
        mock_fact2.to_elt.return_value = mock_fact2_elt
        
        metadata_facts = [mock_fact1, mock_fact2]
        self.mock_taxonomy.get_document_metadata.return_value = metadata_facts
        
        self.element.create_metadata(self.mock_maker, self.mock_taxonomy)
        
        # Verify taxonomy method was called
        self.mock_taxonomy.get_document_metadata.assert_called_once_with(self.mock_data)
        
        # Verify facts were converted to elements and added
        mock_fact1.to_elt.assert_called_once_with(self.element)
        mock_fact2.to_elt.assert_called_once_with(self.element)
        self.mock_hidden.append.assert_any_call(mock_fact1_elt)
        self.mock_hidden.append.assert_any_call(mock_fact2_elt)
    
    def test_create_metadata_skips_unnamed_facts(self):
        """create_metadata should skip facts without names"""
        # Mock facts - some with names, some without
        mock_fact1 = Mock()
        mock_fact1.name = "test:EntityName"
        mock_fact1_elt = Mock()
        mock_fact1.to_elt.return_value = mock_fact1_elt
        
        mock_fact2 = Mock()
        mock_fact2.name = None  # No name
        
        mock_fact3 = Mock()
        mock_fact3.name = ""  # Empty name
        
        mock_fact4 = Mock()
        mock_fact4.name = "test:ValidFact"
        mock_fact4_elt = Mock()
        mock_fact4.to_elt.return_value = mock_fact4_elt
        
        metadata_facts = [mock_fact1, mock_fact2, mock_fact3, mock_fact4]
        self.mock_taxonomy.get_document_metadata.return_value = metadata_facts
        
        self.element.create_metadata(self.mock_maker, self.mock_taxonomy)
        
        # Only facts with names should be processed
        mock_fact1.to_elt.assert_called_once_with(self.element)
        mock_fact2.to_elt.assert_not_called()
        mock_fact3.to_elt.assert_not_called()
        mock_fact4.to_elt.assert_called_once_with(self.element)
        
        # Only 2 elements should be appended
        assert self.mock_hidden.append.call_count == 2
        self.mock_hidden.append.assert_any_call(mock_fact1_elt)
        self.mock_hidden.append.assert_any_call(mock_fact4_elt)
    
    def test_create_metadata_empty_list(self):
        """create_metadata should handle empty metadata list"""
        self.mock_taxonomy.get_document_metadata.return_value = []
        
        self.element.create_metadata(self.mock_maker, self.mock_taxonomy)
        
        # Should not crash, no facts to process
        self.mock_hidden.append.assert_not_called()


class TestBasicElementIntegration:
    """Integration tests for BasicElement"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("integration-test", self.mock_data)
        self.mock_taxonomy = Mock()
    
    def test_complete_ixbrl_generation_workflow(self):
        """Test complete workflow from init to iXBRL output"""
        # Set up comprehensive mocks
        self.mock_taxonomy.get_namespaces.return_value = {"test": "http://test.ns"}
        self.mock_taxonomy.get_schemas.return_value = ["http://schema.test"]
        self.mock_taxonomy.get_document_metadata.return_value = []
        self.mock_taxonomy.contexts = {}
        
        # Mock config values
        mock_title = Mock()
        self.mock_data.get_config.side_effect = lambda key: {
            "report.title": mock_title,
            "metadata.accounting.currency": "EUR",
            "report.style": ".test { color: blue; }"
        }[key]
        self.mock_data.get_config_bool.return_value = False
        
        output = StringIO()
        
        with patch.object(self.element, 'to_ixbrl_elt', return_value=[]):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<?xml version="1.0"?><html>complete</html>'
                
                self.element.to_ixbrl(self.mock_taxonomy, output)
        
        # Verify output was generated
        assert output.getvalue() == '<?xml version="1.0"?><html>complete</html>'
        
        # Verify key methods were involved
        self.mock_data.get_config.assert_any_call("metadata.accounting.currency")
        mock_title.use.assert_called_once()
    
    def test_html_conversion_workflow(self):
        """Test HTML conversion removes iXBRL elements"""
        # Create a simple mock tree structure
        mock_tree = Mock()
        mock_tree.nsmap = {"ix": "http://www.xbrl.org/2013/inlineXBRL"}
        mock_tree.prefix = "ix"
        mock_tree.tag = "{http://www.xbrl.org/2013/inlineXBRL}nonfraction"
        mock_tree.text = "1000"
        mock_tree.keys.return_value = []
        mock_tree.attrib = {}
        mock_tree.iterchildren.return_value = []
        
        # Mock span creation
        self.element.xhtml_maker = Mock()
        mock_span = Mock()
        self.element.xhtml_maker.span.return_value = mock_span
        
        output = StringIO()
        self.mock_data.get_config_bool.return_value = False
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                mock_tostring.return_value = b'<html><span>1000</span></html>'
                
                self.element.to_html(self.mock_taxonomy, output)
        
        # Should have converted ix element to span
        self.element.xhtml_maker.span.assert_called()
        assert output.getvalue() == '<html><span>1000</span></html>'


class TestBasicElementErrorCases:
    """Test error cases and edge conditions"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_data = Mock()
        self.element = BasicElement("error-test", self.mock_data)
    
    def test_init_html_missing_taxonomy_namespaces(self):
        """init_html should handle taxonomy without get_namespaces method"""
        mock_taxonomy = Mock()
        # Remove get_namespaces method
        del mock_taxonomy.get_namespaces
        
        with pytest.raises(AttributeError):
            self.element.init_html(mock_taxonomy)
    
    def test_add_style_missing_xhtml_maker(self):
        """add_style should fail gracefully without xhtml_maker"""
        mock_element = Mock()
        self.mock_data.get_config.return_value = "test css"
        
        # Don't set xhtml_maker
        with pytest.raises(AttributeError):
            self.element.add_style(mock_element)
    
    def test_create_contexts_malformed_dimensions(self):
        """create_contexts should handle malformed dimension data"""
        mock_context = Mock()
        # Return malformed dimension tuple (too few elements)
        mock_context.get_dimensions.return_value = [("incomplete",)]
        
        mock_taxonomy = Mock()
        mock_taxonomy.contexts = {mock_context: "ctx1"}
        mock_taxonomy.contexts_used = {"ctx1"}
        
        # Should raise an error or handle gracefully
        with pytest.raises((IndexError, ValueError)):
            self.element.create_contexts(mock_taxonomy)
    
    def test_to_ixbrl_serialization_error(self):
        """to_ixbrl should handle XML serialization errors"""
        mock_tree = Mock()
        
        with patch.object(self.element, 'to_ixbrl_tree', return_value=mock_tree):
            with patch('ixbrl_reporter.basic_element.etree.tostring') as mock_tostring:
                # Simulate serialization error
                mock_tostring.side_effect = etree.XMLSyntaxError("Invalid XML", None, 0, 0)
                
                output = StringIO()
                self.mock_data.get_config_bool.return_value = False
                
                with pytest.raises(etree.XMLSyntaxError):
                    self.element.to_ixbrl(Mock(), output)
    
    def test_create_entity_with_invalid_segments(self):
        """create_entity should handle invalid segment data"""
        self.element.xbrli_maker = Mock()
        mock_entity = Mock()
        mock_identifier = Mock()
        self.element.xbrli_maker.entity.return_value = mock_entity
        self.element.xbrli_maker.identifier.return_value = mock_identifier
        
        # Pass invalid segment data
        invalid_segments = "not a list"
        
        with pytest.raises(TypeError):
            self.element.create_entity("test", "http://scheme", invalid_segments)