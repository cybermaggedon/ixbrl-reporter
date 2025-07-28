"""
Simplified unit tests for taxonomy module

Testing core functionality without complex initialization dependencies.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date

from ixbrl_reporter.taxonomy import Taxonomy, NamedDimension, TypedDimension
from ixbrl_reporter.datum import StringDatum, DateDatum, MoneyDatum, BoolDatum, CountDatum, NumberDatum, VariableDatum
from ixbrl_reporter.fact import StringFact, DateFact, MoneyFact, BoolFact, CountFact, NumberFact
from ixbrl_reporter.period import Period
from ixbrl_reporter.context import Context
from ixbrl_reporter.config import NoneValue


class TestNamedDimension:
    """Test the NamedDimension class"""
    
    def test_describe(self):
        """Test describing named dimension"""
        dim = NamedDimension()
        dim.dim = "test-dimension"
        dim.value = "test-value"
        
        mock_base = Mock()
        mock_explicit_member = Mock()
        mock_base.xbrldi_maker.explicitMember.return_value = mock_explicit_member
        
        result = dim.describe(mock_base)
        
        mock_base.xbrldi_maker.explicitMember.assert_called_once_with("test-value")
        mock_explicit_member.set.assert_called_once_with("dimension", "test-dimension")
        assert result == mock_explicit_member


class TestTypedDimension:
    """Test the TypedDimension class"""
    
    def test_describe_with_valid_namespace(self):
        """Test describing typed dimension with valid namespace"""
        dim = TypedDimension()
        dim.dim = "test-dimension"
        dim.value = "test-value"
        dim.content = {"tag": "ns:element"}
        
        mock_base = Mock()
        mock_base.nsmap = {"ns": "http://example.com/namespace"}
        mock_typed_member = Mock()
        mock_base.xbrldi_maker.typedMember.return_value = mock_typed_member
        
        with patch('ixbrl_reporter.taxonomy.objectify.ElementMaker') as mock_element_maker:
            mock_maker = Mock()
            mock_element_maker.return_value = mock_maker
            mock_element = Mock()
            mock_maker.return_value = mock_element
            
            result = dim.describe(mock_base)
            
            mock_element_maker.assert_called_once_with(
                annotate=False,
                namespace="http://example.com/namespace"
            )
            mock_maker.assert_called_once_with("element", "test-value")
            mock_typed_member.set.assert_called_once_with("dimension", "test-dimension")
            mock_typed_member.append.assert_called_once_with(mock_element)
            assert result == mock_typed_member
    
    def test_describe_with_invalid_tag_raises_error(self):
        """Test that invalid tag format raises RuntimeError"""
        dim = TypedDimension()
        dim.dim = "test-dimension"
        dim.value = "test-value"
        dim.content = {"tag": "invalid-tag-format"}
        
        mock_base = Mock()
        mock_base.nsmap = {}
        
        with pytest.raises(RuntimeError, match="Could not make sense of typed dimension tag"):
            dim.describe(mock_base)


class TestTaxonomyBasic:
    """Test basic Taxonomy functionality without complex initialization"""
    
    def test_init_basic(self):
        """Test basic Taxonomy initialization"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]  # contexts, metadata
        
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]  # decimals, scale, currency
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        assert taxonomy.cfg == mock_cfg
        assert taxonomy.decimals == 2
        assert taxonomy.scale == 0
        assert taxonomy.currency == "EUR"
        assert taxonomy.next_context_id == 0
        assert isinstance(taxonomy.contexts_used, set)
        assert isinstance(taxonomy.root_context, Context)
        assert isinstance(taxonomy.metadata, dict)
    
    def test_get_context_id_new_context(self):
        """Test getting context ID for new context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        mock_context = Mock()
        
        context_id = taxonomy.get_context_id(mock_context)
        
        assert context_id == "ctxt-0"
        assert taxonomy.contexts[mock_context] == "ctxt-0"
        assert taxonomy.next_context_id == 1
    
    def test_get_context_id_existing_context(self):
        """Test getting context ID for existing context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        mock_context = Mock()
        taxonomy.contexts[mock_context] = "existing-id"
        
        context_id = taxonomy.get_context_id(mock_context)
        
        assert context_id == "existing-id"
    
    def test_create_fact_string_datum(self):
        """Test creating fact from StringDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'create_string_fact') as mock_create:
            mock_fact = Mock()
            mock_create.return_value = mock_fact
            
            datum = StringDatum("test-id", "test-value", Mock())
            result = taxonomy.create_fact(datum)
            
            mock_create.assert_called_once_with(datum)
            assert result == mock_fact
    
    def test_create_fact_variable_datum(self):
        """Test creating fact from VariableDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_metadata_by_id') as mock_get_metadata:
            mock_metadata = Mock()
            mock_get_metadata.return_value = mock_metadata
            
            datum = VariableDatum("test-id", "test-variable", Mock())
            result = taxonomy.create_fact(datum)
            
            mock_get_metadata.assert_called_once_with("test-variable")
            assert result == mock_metadata
    
    def test_create_fact_unknown_datum_raises_error(self):
        """Test that unknown datum type raises RuntimeError"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        unknown_datum = Mock()
        unknown_datum.__class__.__name__ = "UnknownDatum"
        
        with pytest.raises(RuntimeError, match="Not implemented"):
            taxonomy.create_fact(unknown_datum)
    
    def test_get_tag_name(self):
        """Test getting tag name"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]  # init calls
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        # Patch the get method directly for this test
        with patch.object(taxonomy.cfg, 'get', return_value="test-tag") as mock_get:
            result = taxonomy.get_tag_name("test-id")
            
            mock_get.assert_called_with("tags.test-id", mandatory=False)
            assert result == "test-tag"
    
    def test_get_sign_reversed(self):
        """Test getting sign reversed flag"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_cfg.get_bool.return_value = True
        result = taxonomy.get_sign_reversed("test-id")
        
        mock_cfg.get_bool.assert_called_once_with("sign-reversed.test-id", False)
        assert result == True
    
    def test_observe_fact_with_name(self):
        """Test observing fact with name"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_fact = Mock()
        mock_fact.name = "test-fact"
        mock_fact.context = "ctx-1"
        
        taxonomy.observe_fact(mock_fact)
        
        assert "ctx-1" in taxonomy.contexts_used
    
    def test_observe_fact_without_name(self):
        """Test observing fact without name"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_fact = Mock()
        mock_fact.name = None
        mock_fact.context = "ctx-1"
        
        taxonomy.observe_fact(mock_fact)
        
        assert "ctx-1" not in taxonomy.contexts_used
    
    def test_create_money_fact(self):
        """Test creating money fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(taxonomy, 'get_sign_reversed') as mock_get_sign, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.MoneyFact') as mock_money_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_tag.return_value = "money-tag"
            mock_get_sign.return_value = False
            mock_get_dims.return_value = []
            mock_fact = Mock()
            mock_money_fact.return_value = mock_fact
            
            mock_datum = Mock()
            mock_datum.context = Mock()
            mock_datum.id = "test-id"
            mock_datum.value = 1000.0
            
            result = taxonomy.create_money_fact(mock_datum)
            
            mock_money_fact.assert_called_once_with("ctx-1", "money-tag", 1000.0, "EUR", 0, 2, False)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_get_metadata_by_id_existing(self):
        """Test getting existing metadata by ID"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        mock_metadata = Mock()
        taxonomy.metadata["test-id"] = mock_metadata
        
        result = taxonomy.get_metadata_by_id("test-id")
        
        assert result == mock_metadata
    
    def test_get_metadata_by_id_nonexistent(self):
        """Test getting nonexistent metadata returns NoneValue"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        result = taxonomy.get_metadata_by_id("nonexistent")
        
        assert isinstance(result, NoneValue)
    
    def test_get_context_existing(self):
        """Test getting existing context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        mock_context = Mock()
        taxonomy.contexts["test-id"] = mock_context
        
        result = taxonomy.get_context("test-id")
        
        assert result == mock_context
    
    def test_get_context_nonexistent_raises_error(self):
        """Test getting nonexistent context raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with pytest.raises(RuntimeError, match="No such context: nonexistent"):
            taxonomy.get_context("nonexistent")
    
    def test_lookup_dimension_named(self):
        """Test looking up named dimension"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]  # init calls
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        # Set up mock to fail for typed dimension, then succeed for named
        def mock_cfg_get_side_effect(key, mandatory=True):
            if "typed-dimension" in key:
                raise Exception("Not found")
            elif "dimension" in key:
                return "named-dim"
            elif "map" in key:
                return "mapped-value"
            return None
        
        mock_cfg.get.side_effect = mock_cfg_get_side_effect
        
        result = taxonomy.lookup_dimension("test-id", "test-value")
        
        assert isinstance(result, NamedDimension)
        assert result.dim == "named-dim"
        assert result.value == "mapped-value"


class TestTaxonomyFactCreation:
    """Test fact creation methods"""
    
    def setup_method(self):
        """Set up basic taxonomy for each test"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "GBP"]
        
        self.taxonomy = Taxonomy(mock_cfg, mock_data)
    
    def test_create_string_fact(self):
        """Test creating string fact"""
        with patch.object(self.taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(self.taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(self.taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(self.taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.StringFact') as mock_string_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_tag.return_value = "string-tag"
            mock_get_dims.return_value = []
            mock_fact = Mock()
            mock_string_fact.return_value = mock_fact
            
            mock_datum = Mock()
            mock_datum.context = Mock()
            mock_datum.id = "test-id"
            mock_datum.value = "test string"
            
            result = self.taxonomy.create_string_fact(mock_datum)
            
            mock_string_fact.assert_called_once_with("ctx-1", "string-tag", "test string")
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_date_fact(self):
        """Test creating date fact"""
        with patch.object(self.taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(self.taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(self.taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(self.taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.DateFact') as mock_date_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_tag.return_value = "date-tag"
            mock_get_dims.return_value = []
            mock_fact = Mock()
            mock_date_fact.return_value = mock_fact
            
            mock_datum = Mock()
            mock_datum.context = Mock()
            mock_datum.id = "test-id"
            mock_datum.value = date.today()
            
            result = self.taxonomy.create_date_fact(mock_datum)
            
            mock_date_fact.assert_called_once_with("ctx-1", "date-tag", date.today())
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_bool_fact(self):
        """Test creating bool fact"""
        with patch.object(self.taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(self.taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(self.taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(self.taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.BoolFact') as mock_bool_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_tag.return_value = "bool-tag"
            mock_get_dims.return_value = []
            mock_fact = Mock()
            mock_bool_fact.return_value = mock_fact
            
            mock_datum = Mock()
            mock_datum.context = Mock()
            mock_datum.id = "test-id"
            mock_datum.value = True
            
            result = self.taxonomy.create_bool_fact(mock_datum)
            
            mock_bool_fact.assert_called_once_with("ctx-1", "bool-tag", True)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_count_fact(self):
        """Test creating count fact"""
        with patch.object(self.taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(self.taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(self.taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(self.taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.CountFact') as mock_count_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_tag.return_value = "count-tag"
            mock_get_dims.return_value = []
            mock_fact = Mock()
            mock_count_fact.return_value = mock_fact
            
            mock_datum = Mock()
            mock_datum.context = Mock()
            mock_datum.id = "test-id"
            mock_datum.value = 10
            
            result = self.taxonomy.create_count_fact(mock_datum)
            
            mock_count_fact.assert_called_once_with("ctx-1", "count-tag", 10)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_number_fact(self):
        """Test creating number fact"""
        with patch.object(self.taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(self.taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(self.taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(self.taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.NumberFact') as mock_number_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_tag.return_value = "number-tag"
            mock_get_dims.return_value = []
            mock_fact = Mock()
            mock_number_fact.return_value = mock_fact
            
            mock_datum = Mock()
            mock_datum.context = Mock()
            mock_datum.id = "test-id"
            mock_datum.value = 3.14
            
            result = self.taxonomy.create_number_fact(mock_datum)
            
            mock_number_fact.assert_called_once_with("ctx-1", "number-tag", 3.14)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact