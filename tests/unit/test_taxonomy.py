"""
Unit tests for taxonomy module

The taxonomy module handles XBRL taxonomy mapping, context management,
and fact creation for different data types.
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


class TestTaxonomy:
    """Test the Taxonomy class"""
    
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
    
    def test_init_with_contexts_and_metadata(self):
        """Test Taxonomy initialization with contexts and metadata"""
        mock_cfg = Mock()
        mock_context_def = Mock()
        mock_context_def.get.return_value = "test-context"
        mock_metadata_def = Mock()
        mock_metadata_def.get.return_value = "test-metadata"
        mock_cfg.get.side_effect = [[mock_context_def], [mock_metadata_def]]
        
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "GBP"]
        
        with patch.object(Taxonomy, 'load_context') as mock_load_context, \
             patch.object(Taxonomy, 'load_metadata') as mock_load_metadata:
            
            mock_context = Mock()
            mock_load_context.return_value = mock_context
            mock_fact = Mock()
            mock_load_metadata.return_value = mock_fact
            
            taxonomy = Taxonomy(mock_cfg, mock_data)
            
            mock_load_context.assert_called_once()
            mock_load_metadata.assert_called_once()
            assert taxonomy.contexts["test-context"] == mock_context
            assert taxonomy.metadata["test-metadata"] == mock_fact
    
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
    
    def test_create_fact_date_datum(self):
        """Test creating fact from DateDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'create_date_fact') as mock_create:
            mock_fact = Mock()
            mock_create.return_value = mock_fact
            
            datum = DateDatum("test-id", date.today(), Mock())
            result = taxonomy.create_fact(datum)
            
            mock_create.assert_called_once_with(datum)
            assert result == mock_fact
    
    def test_create_fact_money_datum(self):
        """Test creating fact from MoneyDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'create_money_fact') as mock_create:
            mock_fact = Mock()
            mock_create.return_value = mock_fact
            
            datum = MoneyDatum("test-id", 1000.0, Mock())
            result = taxonomy.create_fact(datum)
            
            mock_create.assert_called_once_with(datum)
            assert result == mock_fact
    
    def test_create_fact_bool_datum(self):
        """Test creating fact from BoolDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'create_bool_fact') as mock_create:
            mock_fact = Mock()
            mock_create.return_value = mock_fact
            
            datum = BoolDatum("test-id", True, Mock())
            result = taxonomy.create_fact(datum)
            
            mock_create.assert_called_once_with(datum)
            assert result == mock_fact
    
    def test_create_fact_count_datum(self):
        """Test creating fact from CountDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'create_count_fact') as mock_create:
            mock_fact = Mock()
            mock_create.return_value = mock_fact
            
            datum = CountDatum("test-id", 5, Mock())
            result = taxonomy.create_fact(datum)
            
            mock_create.assert_called_once_with(datum)
            assert result == mock_fact
    
    def test_create_fact_number_datum(self):
        """Test creating fact from NumberDatum"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'create_number_fact') as mock_create:
            mock_fact = Mock()
            mock_create.return_value = mock_fact
            
            datum = NumberDatum("test-id", 3.14, Mock())
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
        mock_cfg.get.side_effect = [[], [], "test-tag"]  # contexts, metadata, tag
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        result = taxonomy.get_tag_name("test-id")
        
        mock_cfg.get.assert_called_with("tags.test-id", mandatory=False)
        assert result == "test-tag"
    
    def test_get_sign_reversed(self):
        """Test getting sign reversed flag"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_cfg.get_bool.return_value = True
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        result = taxonomy.get_sign_reversed("test-id")
        
        mock_cfg.get_bool.assert_called_once_with("sign-reversed.test-id", False)
        assert result == True
    
    def test_get_tag_dimensions(self):
        """Test getting tag dimensions"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], [], ["dim1", "dim2"]]  # contexts, metadata, dimensions
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        result = taxonomy.get_tag_dimensions("test-id")
        
        mock_cfg.get.assert_called_with("segments.test-id", mandatory=False)
        assert result == ["dim1", "dim2"]
    
    def test_get_description_tag_name(self):
        """Test getting description tag name"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], [], "description-tag"]  # contexts, metadata, desc tag
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        result = taxonomy.get_description_tag_name("test-id")
        
        mock_cfg.get.assert_called_with("description-tags.test-id", mandatory=False)
        assert result == "description-tag"
    
    def test_create_description_fact(self):
        """Test creating description fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_description_tag_name') as mock_get_desc_tag, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
             patch('ixbrl_reporter.taxonomy.StringFact') as mock_string_fact:
            
            mock_get_context_id.return_value = "ctx-1"
            mock_get_desc_tag.return_value = "desc-tag"
            mock_get_dims.return_value = ["dim1"]
            mock_fact = Mock()
            mock_string_fact.return_value = mock_fact
            
            mock_meta = Mock()
            mock_meta.id = "test-meta"
            mock_context = Mock()
            
            result = taxonomy.create_description_fact(mock_meta, "test description", mock_context)
            
            mock_string_fact.assert_called_once_with("ctx-1", "desc-tag", "test description")
            assert mock_fact.dimensions == ["dim1"]
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_lookup_dimension_typed(self):
        """Test looking up typed dimension"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], [], "typed-dim-name", {"tag": "ns:elem"}]  # contexts, meta, dim, content
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        result = taxonomy.lookup_dimension("test-id", "test-value")
        
        assert isinstance(result, TypedDimension)
        assert result.dim == "typed-dim-name"
        assert result.content == {"tag": "ns:elem"}
        assert result.value == "test-value"
    
    def test_lookup_dimension_named(self):
        """Test looking up named dimension"""
        mock_cfg = Mock()
        # First call fails (typed), then succeeds for named
        mock_cfg.get.side_effect = [[], [], Exception("Not found"), "named-dim", "mapped-value"]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        result = taxonomy.lookup_dimension("test-id", "test-value")
        
        assert isinstance(result, NamedDimension)
        assert result.dim == "named-dim"
        assert result.value == "mapped-value"
    
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
    
    def test_create_string_fact(self):
        """Test creating string fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
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
            
            result = taxonomy.create_string_fact(mock_datum)
            
            mock_string_fact.assert_called_once_with("ctx-1", "string-tag", "test string")
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_date_fact(self):
        """Test creating date fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
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
            
            result = taxonomy.create_date_fact(mock_datum)
            
            mock_date_fact.assert_called_once_with("ctx-1", "date-tag", date.today())
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_bool_fact(self):
        """Test creating bool fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
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
            
            result = taxonomy.create_bool_fact(mock_datum)
            
            mock_bool_fact.assert_called_once_with("ctx-1", "bool-tag", True)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_count_fact(self):
        """Test creating count fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
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
            
            result = taxonomy.create_count_fact(mock_datum)
            
            mock_count_fact.assert_called_once_with("ctx-1", "count-tag", 10)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_number_fact(self):
        """Test creating number fact"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        with patch.object(taxonomy, 'get_context_id') as mock_get_context_id, \
             patch.object(taxonomy, 'get_tag_name') as mock_get_tag, \
             patch.object(taxonomy, 'get_tag_dimensions') as mock_get_dims, \
             patch.object(taxonomy, 'observe_fact') as mock_observe, \
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
            
            result = taxonomy.create_number_fact(mock_datum)
            
            mock_number_fact.assert_called_once_with("ctx-1", "number-tag", 3.14)
            mock_observe.assert_called_once_with(mock_fact)
            assert result == mock_fact
    
    def test_create_context(self):
        """Test creating context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_cdef = Mock()
        mock_cdef.get_key.return_value = "test-key"
        
        with patch('ixbrl_reporter.taxonomy.Context') as mock_context_class:
            mock_context = Mock()
            mock_context_class.return_value = mock_context
            
            result = taxonomy.create_context(mock_cdef)
            
            mock_context_class.assert_called_once_with(taxonomy, mock_cdef)
            assert mock_context.id == "ctxt-0"
            assert taxonomy.contexts["test-key"] == mock_context
            assert taxonomy.next_context_id == 1
            assert result == mock_context
    
    def test_create_context_existing(self):
        """Test creating context that already exists"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_cdef = Mock()
        mock_cdef.get_key.return_value = "existing-key"
        
        existing_context = Mock()
        taxonomy.contexts["existing-key"] = existing_context
        
        result = taxonomy.create_context(mock_cdef)
        
        assert result == existing_context
        assert taxonomy.next_context_id == 0  # Should not increment
    
    def test_get_namespaces(self):
        """Test getting namespaces"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], [], {"ns": "http://example.com"}]  # contexts, metadata, namespaces
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        result = taxonomy.get_namespaces()
        
        mock_cfg.get.assert_called_with("namespaces")
        assert result == {"ns": "http://example.com"}
    
    def test_get_schemas(self):
        """Test getting schemas"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], [], "http://example.com/schema.xsd"]  # contexts, metadata, schema
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        result = taxonomy.get_schemas()
        
        mock_cfg.get.assert_called_with("schema")
        assert result == "http://example.com/schema.xsd"
    
    def test_get_predefined_contexts(self):
        """Test getting predefined contexts"""
        mock_cfg = Mock()
        mock_context_def = Mock()
        mock_context_def.get.return_value = "ctx-1"
        mock_cfg.get.side_effect = [[mock_context_def], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        taxonomy.contexts["ctx-1"] = Mock()
        
        result = taxonomy.get_predefined_contexts()
        
        assert "ctx-1" in result
        assert result["ctx-1"] == taxonomy.contexts["ctx-1"]
    
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
    
    def test_get_document_metadata(self):
        """Test getting document metadata"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], [], ["meta1", "meta2"]]  # contexts, metadata, doc-metadata
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        taxonomy.metadata["meta1"] = Mock()
        taxonomy.metadata["meta2"] = Mock()
        
        result = taxonomy.get_document_metadata(mock_data)
        
        assert len(result) == 2
        assert taxonomy.metadata["meta1"] in result
        assert taxonomy.metadata["meta2"] in result
    
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
    
    def test_get_all_metadata(self):
        """Test getting all metadata"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        taxonomy.metadata["meta1"] = Mock()
        taxonomy.metadata["meta2"] = Mock()
        
        result = taxonomy.get_all_metadata("ignored-id")
        
        assert len(result) == 2
        assert taxonomy.metadata["meta1"] in result
        assert taxonomy.metadata["meta2"] in result
    
    def test_load_metadata_with_config_value(self):
        """Test loading metadata with config value"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR", "test-value"]  # init + metadata value
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", "test-config", None]  # id, context, config, kind
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            mock_create_fact.assert_called_once()
            assert result == mock_fact
    
    def test_load_metadata_with_direct_value(self):
        """Test loading metadata with direct value"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, "direct-value", None]  # id, context, config, value, kind
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            mock_create_fact.assert_called_once()
            assert result == mock_fact
    
    def test_load_metadata_with_none_value(self):
        """Test loading metadata with NoneValue"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR", NoneValue()]  # init + NoneValue
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", "test-config"]
        mock_ctxts = {"test-context": Mock()}
        
        result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
        
        assert isinstance(result, NoneValue)
    
    def test_load_metadata_date_kind(self):
        """Test loading metadata with date kind"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, "2020-01-01", "date"]
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            # Verify DateDatum was created
            call_args = mock_create_fact.call_args[0][0]
            assert isinstance(call_args, DateDatum)
            assert call_args.id == "test-id"
            assert call_args.value == date(2020, 1, 1)
            assert result == mock_fact
    
    def test_load_metadata_bool_kind(self):
        """Test loading metadata with bool kind"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, True, "bool"]
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            # Verify BoolDatum was created
            call_args = mock_create_fact.call_args[0][0]
            assert isinstance(call_args, BoolDatum)
            assert call_args.id == "test-id"
            assert call_args.value == True
            assert result == mock_fact
    
    def test_load_metadata_money_kind(self):
        """Test loading metadata with money kind"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, 1000.0, "money"]
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            # Verify MoneyDatum was created
            call_args = mock_create_fact.call_args[0][0]
            assert isinstance(call_args, MoneyDatum)
            assert call_args.id == "test-id"
            assert call_args.value == 1000.0
            assert result == mock_fact
    
    def test_load_metadata_count_kind(self):
        """Test loading metadata with count kind"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, 5, "count"]
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            # Verify CountDatum was created
            call_args = mock_create_fact.call_args[0][0]
            assert isinstance(call_args, CountDatum)
            assert call_args.id == "test-id"
            assert call_args.value == 5
            assert result == mock_fact
    
    def test_load_metadata_number_kind(self):
        """Test loading metadata with number kind"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, 3.14, "number"]
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            # Verify NumberDatum was created
            call_args = mock_create_fact.call_args[0][0]
            assert isinstance(call_args, NumberDatum)
            assert call_args.id == "test-id"
            assert call_args.value == 3.14
            assert result == mock_fact
    
    def test_load_metadata_string_kind_default(self):
        """Test loading metadata with default string kind"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["test-id", "test-context", None, "test string", None]  # no kind
        mock_context = Mock()
        mock_ctxts = {"test-context": mock_context}
        
        with patch.object(taxonomy, 'create_fact') as mock_create_fact:
            mock_fact = Mock()
            mock_create_fact.return_value = mock_fact
            
            result = taxonomy.load_metadata(mock_data, mock_defn, mock_ctxts)
            
            # Verify StringDatum was created (default)
            call_args = mock_create_fact.call_args[0][0]
            assert isinstance(call_args, StringDatum)
            assert call_args.id == "test-id"
            assert call_args.value == "test string"
            assert result == mock_fact
    
    def test_load_context_from_existing(self):
        """Test loading context from existing context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = ["from-context", None, None, None, None]  # from, entity, period, instant, segments
        
        mock_existing_context = Mock()
        mock_contexts = {"from-context": mock_existing_context}
        
        result = taxonomy.load_context(mock_defn, mock_data, mock_contexts)
        
        assert result == mock_existing_context
    
    def test_load_context_with_entity(self):
        """Test loading context with entity"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR", "http://example.com", "12345"]  # init + entity data
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = [None, "entity-scheme", "scheme-config", "entity-id", "id-config", None, None, None]
        
        mock_contexts = {}
        mock_root_context = Mock()
        mock_context_with_entity = Mock()
        mock_root_context.with_entity.return_value = mock_context_with_entity
        taxonomy.root_context = mock_root_context
        
        result = taxonomy.load_context(mock_defn, mock_data, mock_contexts)
        
        mock_root_context.with_entity.assert_called_once_with("http://example.com", "12345")
        assert result == mock_context_with_entity
    
    def test_load_context_with_period(self):
        """Test loading context with period"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR", {"start": "2020-01-01", "end": "2020-12-31"}]  # init + period
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = [None, None, "period-config", None, None]
        
        mock_contexts = {}
        mock_root_context = Mock()
        mock_context_with_period = Mock()
        mock_root_context.with_period.return_value = mock_context_with_period
        taxonomy.root_context = mock_root_context
        
        with patch('ixbrl_reporter.taxonomy.Period.load') as mock_period_load:
            mock_period = Mock()
            mock_period_load.return_value = mock_period
            
            result = taxonomy.load_context(mock_defn, mock_data, mock_contexts)
            
            mock_period_load.assert_called_once_with({"start": "2020-01-01", "end": "2020-12-31"})
            mock_root_context.with_period.assert_called_once_with(mock_period)
            assert result == mock_context_with_period
    
    def test_load_context_with_instant(self):
        """Test loading context with instant"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        mock_data.get_config_date.return_value = date(2020, 12, 31)
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = [None, None, None, "instant-config", None]
        
        mock_contexts = {}
        mock_root_context = Mock()
        mock_context_with_instant = Mock()
        mock_root_context.with_instant.return_value = mock_context_with_instant
        taxonomy.root_context = mock_root_context
        
        result = taxonomy.load_context(mock_defn, mock_data, mock_contexts)
        
        mock_data.get_config_date.assert_called_once_with("instant-config")
        mock_root_context.with_instant.assert_called_once_with(date(2020, 12, 31))
        assert result == mock_context_with_instant
    
    def test_load_context_with_segments(self):
        """Test loading context with segments"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR", "segment-value"]  # init + segment value
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = [None, None, None, None, [{"segment-key": "segment-config"}]]
        
        mock_contexts = {}
        mock_root_context = Mock()
        mock_context_with_segments = Mock()
        mock_root_context.with_segments.return_value = mock_context_with_segments
        taxonomy.root_context = mock_root_context
        
        result = taxonomy.load_context(mock_defn, mock_data, mock_contexts)
        
        mock_root_context.with_segments.assert_called_once_with([("segment-key", "segment-value")])
        assert result == mock_context_with_segments
    
    def test_load_context_with_invalid_segments(self):
        """Test loading context with invalid segments raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = [None, None, None, None, "not-a-list"]
        
        with pytest.raises(RuntimeError, match="segments should be array"):
            taxonomy.load_context(mock_defn, mock_data, {})
    
    def test_load_context_with_multi_item_segment(self):
        """Test loading context with multi-item segment raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [[], []]
        mock_data = Mock()
        mock_data.get_config.side_effect = [2, 0, "EUR"]
        
        taxonomy = Taxonomy(mock_cfg, mock_data)
        
        mock_defn = Mock()
        mock_defn.get.side_effect = [None, None, None, None, [{"key1": "val1", "key2": "val2"}]]
        
        with pytest.raises(RuntimeError, match="segments should be array of single item maps"):
            taxonomy.load_context(mock_defn, mock_data, {})