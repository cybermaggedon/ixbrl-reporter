"""
Unit tests for ixbrl_reporter.computation module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import date, timedelta
import json

from ixbrl_reporter.computation import (
    Metadata, Computable, Line, Constant, Group, Sum, AbsOperation,
    ApportionOperation, RoundOperation, FactorOperation, Comparison,
    get_computation, create_uuid, ResultSet,
    IN_YEAR, AT_START, AT_END,
    ROUND_DOWN, ROUND_UP, ROUND_NEAREST,
    CMP_LESS, CMP_LESS_EQUAL, CMP_GREATER, CMP_GREATER_EQUAL
)


class TestHelperFunctions:
    """Test module-level helper functions"""
    
    def test_create_uuid(self):
        """create_uuid should return valid UUID string"""
        uuid1 = create_uuid()
        uuid2 = create_uuid()
        
        # Should be strings
        assert isinstance(uuid1, str)
        assert isinstance(uuid2, str)
        
        # Should be different
        assert uuid1 != uuid2
        
        # Should be UUID format (36 chars with dashes)
        assert len(uuid1) == 36
        assert len(uuid2) == 36
        assert uuid1.count('-') == 4
        assert uuid2.count('-') == 4
    
    def test_get_computation_with_string(self):
        """get_computation should return existing computation for string key"""
        mock_comp = Mock()
        comps = {"test_comp": mock_comp}
        
        result = get_computation("test_comp", comps, None, None, None)
        
        assert result == mock_comp
    
    def test_get_computation_with_dict(self):
        """get_computation should create new computation for dict config"""
        mock_config = {"kind": "sum", "inputs": []}
        mock_comp = Mock()
        
        with patch.object(Computable, 'load', return_value=mock_comp) as mock_load:
            result = get_computation(mock_config, {}, "context", "data", "gcfg")
        
        mock_load.assert_called_once_with(mock_config, {}, "context", "data", "gcfg")
        assert result == mock_comp


class TestConstants:
    """Test module constants"""
    
    def test_period_constants(self):
        """Test period type constants"""
        assert IN_YEAR == 1
        assert AT_START == 2
        assert AT_END == 3
    
    def test_rounding_constants(self):
        """Test rounding direction constants"""
        assert ROUND_DOWN == 1
        assert ROUND_UP == 2
        assert ROUND_NEAREST == 3
    
    def test_comparison_constants(self):
        """Test comparison type constants"""
        assert CMP_LESS == 1
        assert CMP_LESS_EQUAL == 2
        assert CMP_GREATER == 3
        assert CMP_GREATER_EQUAL == 4


class TestResultSet:
    """Test ResultSet class functionality"""
    
    def test_result_set_creation(self):
        """ResultSet should be created and behave like dict"""
        rs = ResultSet()
        
        # Should behave like dict
        assert len(rs) == 0
        
        # Should support dict operations
        rs["test"] = "value"
        assert rs["test"] == "value"
        assert len(rs) == 1
    
    def test_result_set_set_method(self):
        """ResultSet.set should store key-value pairs"""
        rs = ResultSet()
        
        rs.set("key1", "value1")
        rs.set("key2", "value2")
        
        assert rs["key1"] == "value1"
        assert rs["key2"] == "value2"
        assert len(rs) == 2
    
    def test_result_set_get_method(self):
        """ResultSet.get should retrieve values or return None"""
        rs = ResultSet()
        rs["existing"] = "value"
        
        assert rs.get("existing") == "value"
        assert rs.get("nonexistent") is None
        assert rs.get("nonexistent", "default") == "default"


class TestMetadata:
    """Test Metadata class functionality"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_context = Mock()
        self.mock_gcfg = Mock()
    
    def test_metadata_init(self):
        """Metadata should initialize with all parameters"""
        metadata = Metadata(
            id="test-id",
            description="Test Description",
            context=self.mock_context,
            segments=[("dim1", "val1")],
            period=AT_END,
            note="Test note"
        )
        
        assert metadata.id == "test-id"
        assert metadata.description == "Test Description"
        assert metadata.context == self.mock_context
        assert metadata.segments == [("dim1", "val1")]
        assert metadata.period == AT_END
        assert metadata.note == "Test note"
    
    def test_metadata_load_basic(self):
        """Metadata.load should create metadata from basic config"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", None, False): "test-id",
            ("description", "?"): "Test Desc",
            ("period", "at-end"): "at-end",
            ("segments", []): [],
            ("note", None, False): None
        }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
        
        metadata = Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
        
        assert metadata.id == "test-id"
        assert metadata.description == "Test Desc"
        assert metadata.context == self.mock_context
        assert metadata.segments == []
        assert metadata.period == AT_END
        assert metadata.note is None
    
    def test_metadata_load_generates_uuid_when_no_id(self):
        """Metadata.load should generate UUID when id is None"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", None, False): None,
            ("description", "?"): "Test Desc",
            ("period", "at-end"): "at-end",
            ("segments", []): [],
            ("note", None, False): None
        }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
        
        with patch('ixbrl_reporter.computation.create_uuid', return_value='uuid-123') as mock_uuid:
            metadata = Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
        
        mock_uuid.assert_called_once()
        assert metadata.id == "uuid-123"
    
    def test_metadata_load_period_types(self):
        """Metadata.load should handle different period types"""
        test_cases = [
            ("in-year", IN_YEAR),
            ("at-start", AT_START),
            ("at-end", AT_END),
            ("invalid", AT_END)  # Default fallback
        ]
        
        for period_str, expected_const in test_cases:
            mock_cfg = Mock()
            mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
                ("id", None, False): "test-id",
                ("description", "?"): "Test",
                ("period", "at-end"): period_str,
                ("segments", []): [],
                ("note", None, False): None
            }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
            
            metadata = Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
            assert metadata.period == expected_const
    
    def test_metadata_load_segments_processing(self):
        """Metadata.load should process segments correctly"""
        mock_cfg = Mock()
        segments_config = [
            {"dimension1": "value1"},
            {"dimension2": "mapped_value"}
        ]
        
        # Mock gcfg to return mapped value for second segment
        self.mock_gcfg.get.side_effect = lambda key, default: {
            "mapped_value": "actual_value"
        }.get(key, default)
        
        mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", None, False): "test-id",
            ("description", "?"): "Test",
            ("period", "at-end"): "at-end",
            ("segments", []): segments_config,
            ("note", None, False): None
        }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
        
        metadata = Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
        
        assert metadata.segments == [
            ("dimension1", "value1"),
            ("dimension2", "actual_value")
        ]
    
    def test_metadata_load_segments_validation_not_list(self):
        """Metadata.load should raise error if segments is not list"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", None, False): "test-id",
            ("description", "?"): "Test",
            ("period", "at-end"): "at-end",
            ("segments", []): "not-a-list",  # Invalid
            ("note", None, False): None
        }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
        
        with pytest.raises(RuntimeError, match="segments should be list of single-item maps"):
            Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
    
    def test_metadata_load_segments_validation_multiple_items(self):
        """Metadata.load should raise error if segment has multiple items"""
        mock_cfg = Mock()
        segments_config = [
            {"dim1": "val1", "dim2": "val2"}  # Multiple items - invalid
        ]
        
        mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", None, False): "test-id",
            ("description", "?"): "Test",
            ("period", "at-end"): "at-end",
            ("segments", []): segments_config,
            ("note", None, False): None
        }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
        
        with pytest.raises(RuntimeError, match="segments should be list of single-item maps"):
            Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
    
    def test_metadata_load_with_note(self):
        """Metadata.load should handle note field"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, default=None, mandatory=True: {
            ("id", None, False): "test-id",
            ("description", "?"): "Test",
            ("period", "at-end"): "at-end",
            ("segments", []): [],
            ("note", None, False): 12345  # Will be converted to string
        }.get((key, default, mandatory) if default is not None or not mandatory else (key, default), default)
        
        metadata = Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
        
        assert metadata.note == "12345"
    
    def test_metadata_get_context_at_start(self):
        """get_context should handle AT_START period correctly"""
        metadata = Metadata("id", "desc", self.mock_context, [], AT_START, None)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        mock_instant_context = Mock()
        self.mock_context.with_instant.return_value = mock_instant_context
        
        result = metadata.get_context(start_date, end_date)
        
        # Should use day before start date
        expected_date = start_date - timedelta(days=1)
        self.mock_context.with_instant.assert_called_once_with(expected_date)
        assert result == mock_instant_context
    
    def test_metadata_get_context_at_end(self):
        """get_context should handle AT_END period correctly"""
        metadata = Metadata("id", "desc", self.mock_context, [], AT_END, None)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        mock_instant_context = Mock()
        self.mock_context.with_instant.return_value = mock_instant_context
        
        result = metadata.get_context(start_date, end_date)
        
        self.mock_context.with_instant.assert_called_once_with(end_date)
        assert result == mock_instant_context
    
    def test_metadata_get_context_in_year(self):
        """get_context should handle IN_YEAR period correctly"""
        metadata = Metadata("id", "desc", self.mock_context, [], IN_YEAR, None)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        mock_period_context = Mock()
        self.mock_context.with_period.return_value = mock_period_context
        
        with patch('ixbrl_reporter.computation.Period') as mock_period_class:
            mock_period = Mock()
            mock_period_class.return_value = mock_period
            
            result = metadata.get_context(start_date, end_date)
        
        mock_period_class.assert_called_once_with("", start_date, end_date)
        self.mock_context.with_period.assert_called_once_with(mock_period)
        assert result == mock_period_context
    
    def test_metadata_get_context_with_segments(self):
        """get_context should apply segments to context"""
        segments = [("dim1", "val1"), ("dim2", "val2")]
        metadata = Metadata("id", "desc", self.mock_context, segments, AT_END, None)
        
        mock_instant_context = Mock()
        mock_segmented_context = Mock()
        self.mock_context.with_instant.return_value = mock_instant_context
        mock_instant_context.with_segments.return_value = mock_segmented_context
        
        result = metadata.get_context(date(2023, 1, 1), date(2023, 12, 31))
        
        mock_instant_context.with_segments.assert_called_once_with(segments)
        assert result == mock_segmented_context
    
    def test_metadata_result(self):
        """result method should retrieve value from result set"""
        metadata = Metadata("test-id", "desc", None, [], AT_END, None)
        
        mock_result = Mock()
        mock_result.get.return_value = "test-value"
        
        result = metadata.result(mock_result)
        
        mock_result.get.assert_called_once_with("test-id")
        assert result == "test-value"


class TestComputable:
    """Test Computable base class"""
    
    def test_computable_compute_not_implemented(self):
        """Computable.compute should raise NotImplementedError"""
        comp = Computable()
        
        with pytest.raises(RuntimeError, match="Not implemented"):
            comp.compute(None, None, None, None)
    
    def test_computable_load_group(self):
        """Computable.load should create Group for kind='group'"""
        mock_cfg = Mock()
        mock_cfg.get.return_value = "group"
        
        with patch.object(Group, 'load') as mock_group_load:
            mock_group_load.return_value = Mock()
            
            result = Computable.load(mock_cfg, "comps", "context", "data", "gcfg")
            
            mock_group_load.assert_called_once_with(mock_cfg, "comps", "context", "data", "gcfg")
    
    def test_computable_load_sum(self):
        """Computable.load should create Sum for kind='sum'"""
        mock_cfg = Mock()
        mock_cfg.get.return_value = "sum"
        
        with patch.object(Sum, 'load') as mock_sum_load:
            mock_sum_load.return_value = Mock()
            
            result = Computable.load(mock_cfg, "comps", "context", "data", "gcfg")
            
            mock_sum_load.assert_called_once_with(mock_cfg, "comps", "context", "data", "gcfg")
    
    def test_computable_load_all_kinds(self):
        """Computable.load should handle all computation kinds"""
        test_cases = [
            ("group", Group),
            ("sum", Sum),
            ("abs", AbsOperation),
            ("apportion", ApportionOperation),
            ("round", RoundOperation),
            ("factor", FactorOperation),
            ("compare", Comparison),
            ("line", Line),
            ("constant", Constant)
        ]
        
        for kind, expected_class in test_cases:
            mock_cfg = Mock()
            mock_cfg.get.return_value = kind
            
            with patch.object(expected_class, 'load') as mock_load:
                mock_load.return_value = Mock()
                
                Computable.load(mock_cfg, "comps", "context", "data", "gcfg")
                
                mock_load.assert_called_once_with(mock_cfg, "comps", "context", "data", "gcfg")
    
    def test_computable_load_unknown_kind(self):
        """Computable.load should raise error for unknown kind"""
        mock_cfg = Mock()
        mock_cfg.get.return_value = "unknown_kind"
        
        with pytest.raises(RuntimeError, match="Don't understand computable type 'unknown_kind'"):
            Computable.load(mock_cfg, {}, None, None, None)


class TestLine:
    """Test Line computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "line-1"
        self.mock_metadata.context = Mock()
        self.mock_metadata.segments = []
        self.accounts = ["Assets:Bank", "Assets:Cash"]
    
    def test_line_init(self):
        """Line should initialize with metadata, accounts, and reverse flag"""
        line = Line(self.mock_metadata, self.accounts, reverse=True)
        
        assert line.metadata == self.mock_metadata
        assert line.accounts == self.accounts
        assert line.reverse is True
    
    def test_line_load_basic(self):
        """Line.load should create Line from config"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key: {
            "accounts": ["Assets:Bank"]
        }[key]
        mock_cfg.get_bool.return_value = False
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata) as mock_meta_load:
            line = Line.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        mock_meta_load.assert_called_once_with(mock_cfg, "comps", "context", "data", "gcfg")
        assert line.metadata == self.mock_metadata
        assert line.accounts == ["Assets:Bank"]
        assert line.reverse is False
    
    def test_line_load_with_reverse_sign(self):
        """Line.load should handle reverse-sign flag"""
        mock_cfg = Mock()
        mock_cfg.get.return_value = ["Assets:Bank"]
        mock_cfg.get_bool.return_value = True
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            line = Line.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        mock_cfg.get_bool.assert_called_once_with("reverse-sign", False)
        assert line.reverse is True
    
    def test_line_compute_at_end_period(self):
        """Line.compute should handle AT_END period correctly"""
        self.mock_metadata.period = AT_END
        
        # Set up mocks
        mock_context = Mock()
        mock_session = Mock()
        mock_account = Mock()
        mock_result = Mock()
        mock_datum = Mock()
        
        self.mock_metadata.context.with_instant.return_value = mock_context
        mock_session.get_account.return_value = mock_account
        mock_session.get_splits.return_value = [
            {"amount": 100.0},
            {"amount": 200.0}
        ]
        mock_session.is_debit.return_value = True  # Debit account
        mock_context.create_money_datum.return_value = mock_datum
        
        line = Line(self.mock_metadata, ["Assets:Bank"], reverse=False)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        result = line.compute(mock_session, start_date, end_date, mock_result)
        
        # Verify context creation
        self.mock_metadata.context.with_instant.assert_called_once_with(end_date)
        
        # Verify account processing
        mock_session.get_account.assert_called_once_with(None, "Assets:Bank")
        mock_session.get_splits.assert_called_once_with(
            mock_account, date(1970, 1, 1), end_date
        )
        
        # Verify calculation (debit account, so multiply by -1)
        expected_total = -300.0  # (100 + 200) * -1 for debit
        assert result == expected_total
        
        # Verify result storage
        mock_context.create_money_datum.assert_called_once_with("line-1", expected_total)
        mock_result.set.assert_called_once_with("line-1", mock_datum)
    
    def test_line_compute_at_start_period(self):
        """Line.compute should handle AT_START period correctly"""
        self.mock_metadata.period = AT_START
        
        mock_context = Mock()
        mock_session = Mock()
        mock_account = Mock()
        mock_result = Mock()
        
        self.mock_metadata.context.with_instant.return_value = mock_context
        mock_session.get_account.return_value = mock_account
        mock_session.get_splits.return_value = [{"amount": 100.0}]
        mock_session.is_debit.return_value = False  # Credit account
        
        line = Line(self.mock_metadata, ["Liabilities:Loan"], reverse=False)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        line.compute(mock_session, start_date, end_date, mock_result)
        
        # Should use start date for context
        self.mock_metadata.context.with_instant.assert_called_once_with(start_date)
        
        # Should query from 1970 to day before start
        expected_end = start_date - timedelta(days=1)
        mock_session.get_splits.assert_called_once_with(
            mock_account, date(1970, 1, 1), expected_end
        )
    
    def test_line_compute_in_year_period(self):
        """Line.compute should handle IN_YEAR period correctly"""
        self.mock_metadata.period = IN_YEAR
        
        mock_context = Mock()
        mock_session = Mock()
        mock_account = Mock()
        mock_result = Mock()
        
        self.mock_metadata.context.with_period.return_value = mock_context
        mock_session.get_account.return_value = mock_account
        mock_session.get_splits.return_value = []
        mock_session.is_debit.return_value = False
        
        line = Line(self.mock_metadata, ["Revenue:Sales"], reverse=False)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        with patch('ixbrl_reporter.computation.Period') as mock_period_class:
            mock_period = Mock()
            mock_period_class.return_value = mock_period
            
            line.compute(mock_session, start_date, end_date, mock_result)
        
        # Should create period and use it for context
        mock_period_class.assert_called_once_with("", start_date, end_date)
        self.mock_metadata.context.with_period.assert_called_once_with(mock_period)
        
        # Should query for exact period
        mock_session.get_splits.assert_called_once_with(mock_account, start_date, end_date)
    
    def test_line_compute_multiple_accounts(self):
        """Line.compute should sum multiple accounts"""
        self.mock_metadata.period = AT_END
        
        mock_session = Mock()
        mock_account1 = Mock()
        mock_account2 = Mock()
        mock_result = Mock()
        
        # Set up account retrieval
        mock_session.get_account.side_effect = [mock_account1, mock_account2]
        
        # Set up splits for each account
        mock_session.get_splits.side_effect = [
            [{"amount": 100.0}, {"amount": 50.0}],  # Account 1: 150
            [{"amount": 200.0}]  # Account 2: 200
        ]
        
        # Both are credit accounts (no sign flip)
        mock_session.is_debit.return_value = False
        
        line = Line(self.mock_metadata, ["Revenue:Sales", "Revenue:Interest"], reverse=False)
        
        result = line.compute(mock_session, date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should sum both accounts: 150 + 200 = 350
        assert result == 350.0
        
        # Should have called get_account for both accounts
        assert mock_session.get_account.call_count == 2
        assert mock_session.get_splits.call_count == 2
    
    def test_line_compute_with_reverse_sign(self):
        """Line.compute should apply reverse sign when specified"""
        self.mock_metadata.period = AT_END
        
        mock_session = Mock()
        mock_account = Mock()
        mock_result = Mock()
        
        mock_session.get_account.return_value = mock_account
        mock_session.get_splits.return_value = [{"amount": 100.0}]
        mock_session.is_debit.return_value = False  # Credit account (no flip)
        
        line = Line(self.mock_metadata, ["Revenue:Sales"], reverse=True)
        
        result = line.compute(mock_session, date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should apply reverse: 100 * -1 = -100
        assert result == -100.0
    
    def test_line_compute_with_segments(self):
        """Line.compute should apply segments to context"""
        self.mock_metadata.period = AT_END
        self.mock_metadata.segments = [("dim1", "val1")]
        
        mock_session = Mock()
        mock_account = Mock()
        mock_result = Mock()
        mock_context = Mock()
        mock_segmented_context = Mock()
        
        self.mock_metadata.context.with_instant.return_value = mock_context
        mock_context.with_segments.return_value = mock_segmented_context
        mock_session.get_account.return_value = mock_account
        mock_session.get_splits.return_value = []
        mock_session.is_debit.return_value = False
        
        line = Line(self.mock_metadata, ["Revenue:Sales"], reverse=False)
        
        line.compute(mock_session, date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should apply segments to context
        mock_context.with_segments.assert_called_once_with([("dim1", "val1")])
        
        # Should use segmented context for datum creation
        mock_segmented_context.create_money_datum.assert_called_once_with("line-1", 0.0)
    
    def test_line_get_output_empty_accounts(self):
        """Line.get_output should return NilResult for empty accounts"""
        line = Line(self.mock_metadata, [], reverse=False)
        
        mock_result = Mock()
        mock_datum = Mock()
        self.mock_metadata.result.return_value = mock_datum
        
        with patch('ixbrl_reporter.computation.NilResult') as mock_nil_result:
            mock_nil_instance = Mock()
            mock_nil_result.return_value = mock_nil_instance
            
            output = line.get_output(mock_result)
        
        mock_nil_result.assert_called_once_with(line, mock_datum)
        assert output == mock_nil_instance
    
    def test_line_get_output_with_accounts(self):
        """Line.get_output should return TotalResult for non-empty accounts"""
        line = Line(self.mock_metadata, ["Assets:Bank"], reverse=False)
        
        mock_result = Mock()
        mock_datum = Mock()
        self.mock_metadata.result.return_value = mock_datum
        
        with patch('ixbrl_reporter.computation.TotalResult') as mock_total_result:
            mock_total_instance = Mock()
            mock_total_result.return_value = mock_total_instance
            
            output = line.get_output(mock_result)
        
        mock_total_result.assert_called_once_with(line, mock_datum, items=[])
        assert output == mock_total_instance


class TestConstant:
    """Test Constant computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "const-1"
        self.values = {
            "2023-12-31": 1000.0,
            "2024-12-31": 1500.0
        }
    
    def test_constant_init(self):
        """Constant should initialize with metadata and values"""
        constant = Constant(self.mock_metadata, self.values)
        
        assert constant.metadata == self.mock_metadata
        assert constant.values == self.values
    
    def test_constant_load(self):
        """Constant.load should create Constant from config"""
        mock_cfg = Mock()
        mock_cfg.get.return_value = self.values
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata) as mock_meta_load:
            constant = Constant.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        mock_meta_load.assert_called_once_with(mock_cfg, "comps", "context", "data", "gcfg")
        mock_cfg.get.assert_called_once_with("values")
        assert constant.metadata == self.mock_metadata
        assert constant.values == self.values
    
    def test_constant_compute(self):
        """Constant.compute should return value for specified end date"""
        mock_context = Mock()
        mock_datum = Mock()
        mock_result = Mock()
        
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        constant = Constant(self.mock_metadata, self.values)
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        result = constant.compute("session", start_date, end_date, mock_result)
        
        # Should get context for the period
        self.mock_metadata.get_context.assert_called_once_with(start_date, end_date)
        
        # Should look up value by end date string
        assert result == 1000.0
        
        # Should create datum and store result
        mock_context.create_money_datum.assert_called_once_with("const-1", 1000.0)
        mock_result.set.assert_called_once_with("const-1", mock_datum)
    
    def test_constant_compute_different_date(self):
        """Constant.compute should return correct value for different date"""
        mock_context = Mock()
        mock_result = Mock()
        
        self.mock_metadata.get_context.return_value = mock_context
        
        constant = Constant(self.mock_metadata, self.values)
        
        end_date = date(2024, 12, 31)
        result = constant.compute("session", date(2024, 1, 1), end_date, mock_result)
        
        # Should return value for 2024
        assert result == 1500.0
    
    def test_constant_get_output(self):
        """Constant.get_output should return SimpleValue result"""
        constant = Constant(self.mock_metadata, self.values)
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        with patch('ixbrl_reporter.computation.SimpleValue') as mock_simple_value:
            mock_simple_instance = Mock()
            mock_simple_value.return_value = mock_simple_instance
            
            output = constant.get_output(mock_result)
        
        mock_result.get.assert_called_once_with("const-1")
        mock_simple_value.assert_called_once_with(constant, mock_datum)
        assert output == mock_simple_instance


class TestGroup:
    """Test Group computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "group-1"
        self.mock_metadata.get_context.return_value = Mock()
    
    def test_group_init_default(self):
        """Group should initialize with empty inputs by default"""
        group = Group(self.mock_metadata)
        
        assert group.metadata == self.mock_metadata
        assert group.inputs == []
    
    def test_group_init_with_inputs(self):
        """Group should initialize with provided inputs"""
        inputs = [Mock(), Mock()]
        group = Group(self.mock_metadata, inputs)
        
        assert group.inputs == inputs
    
    def test_group_load_basic(self):
        """Group.load should create Group from config"""
        mock_cfg = Mock()
        mock_input_configs = ["input1", {"kind": "sum"}]
        mock_cfg.get.return_value = mock_input_configs
        
        mock_hide_config = Mock()
        mock_hide_config.use = Mock()
        mock_cfg.get.side_effect = lambda key, default=None: {
            "inputs": mock_input_configs,
            "hide-breakdown": mock_hide_config
        }.get(key, default if default is not None else Mock())
        
        mock_input1 = Mock()
        mock_input2 = Mock()
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation') as mock_get_comp:
                mock_get_comp.side_effect = [mock_input1, mock_input2]
                
                group = Group.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        # Should have created group with metadata
        assert group.metadata == self.mock_metadata
        
        # Should have loaded inputs
        assert len(group.inputs) == 2
        assert mock_get_comp.call_count == 2
        
        # Should have processed hide-breakdown config
        mock_hide_config.use.assert_called_once()
    
    def test_group_is_single_line_empty(self):
        """Group.is_single_line should return True for empty inputs"""
        group = Group(self.mock_metadata, [])
        
        assert group.is_single_line() is True
    
    def test_group_is_single_line_with_inputs(self):
        """Group.is_single_line should return False for non-empty inputs"""
        group = Group(self.mock_metadata, [Mock()])
        
        assert group.is_single_line() is False
    
    def test_group_add(self):
        """Group.add should append input to inputs list"""
        group = Group(self.mock_metadata, [])
        mock_input = Mock()
        
        group.add(mock_input)
        
        assert len(group.inputs) == 1
        assert group.inputs[0] == mock_input
    
    def test_group_compute(self):
        """Group.compute should sum all input computations"""
        mock_input1 = Mock()
        mock_input2 = Mock()
        mock_input1.compute.return_value = 100.0
        mock_input2.compute.return_value = 200.0
        
        group = Group(self.mock_metadata, [mock_input1, mock_input2])
        
        mock_context = Mock()
        mock_datum = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        mock_result = Mock()
        
        start_date = date(2023, 1, 1)
        end_date = date(2023, 12, 31)
        
        result = group.compute("accounts", start_date, end_date, mock_result)
        
        # Should compute all inputs
        mock_input1.compute.assert_called_once_with("accounts", start_date, end_date, mock_result)
        mock_input2.compute.assert_called_once_with("accounts", start_date, end_date, mock_result)
        
        # Should sum results
        assert result == 300.0
        
        # Should store result
        mock_context.create_money_datum.assert_called_once_with("group-1", 300.0)
        mock_result.set.assert_called_once_with("group-1", mock_datum)
    
    def test_group_compute_empty_inputs(self):
        """Group.compute should return 0 for empty inputs"""
        group = Group(self.mock_metadata, [])
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        result = group.compute("accounts", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        assert result == 0
    
    def test_group_get_output_empty_inputs(self):
        """Group.get_output should return NilResult for empty inputs"""
        group = Group(self.mock_metadata, [])
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        with patch('ixbrl_reporter.computation.NilResult') as mock_nil_result:
            mock_nil_instance = Mock()
            mock_nil_result.return_value = mock_nil_instance
            
            output = group.get_output(mock_result)
        
        mock_nil_result.assert_called_once_with(group, mock_datum)
        assert output == mock_nil_instance
    
    def test_group_get_output_hidden_breakdown(self):
        """Group.get_output should return SimpleResult for hidden breakdown"""
        mock_input = Mock()
        group = Group(self.mock_metadata, [mock_input])
        group.hide_breakdown = True
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = group.get_output(mock_result)
        
        mock_simple_result.assert_called_once_with(group, mock_datum)
        assert output == mock_simple_instance
    
    def test_group_get_output_with_breakdown(self):
        """Group.get_output should return BreakdownResult for visible breakdown"""
        mock_input1 = Mock()
        mock_input2 = Mock()
        group = Group(self.mock_metadata, [mock_input1, mock_input2])
        group.hide_breakdown = False
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_output1 = Mock()
        mock_output2 = Mock()
        mock_input1.get_output.return_value = mock_output1
        mock_input2.get_output.return_value = mock_output2
        
        with patch('ixbrl_reporter.computation.BreakdownResult') as mock_breakdown_result:
            mock_breakdown_instance = Mock()
            mock_breakdown_result.return_value = mock_breakdown_instance
            
            output = group.get_output(mock_result)
        
        # Should get output from all inputs
        mock_input1.get_output.assert_called_once_with(mock_result)
        mock_input2.get_output.assert_called_once_with(mock_result)
        
        # Should create breakdown with all outputs
        mock_breakdown_result.assert_called_once_with(
            group, mock_datum, items=[mock_output1, mock_output2]
        )
        assert output == mock_breakdown_instance


class TestSum:
    """Test Sum computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "sum-1"
    
    def test_sum_init(self):
        """Sum should initialize with metadata and inputs"""
        inputs = [Mock(), Mock()]
        sum_comp = Sum(self.mock_metadata, inputs)
        
        assert sum_comp.metadata == self.mock_metadata
        assert sum_comp.inputs == inputs
    
    def test_sum_load(self):
        """Sum.load should create Sum from config"""
        mock_cfg = Mock()
        mock_input_configs = ["input1", "input2"]
        mock_cfg.get.return_value = mock_input_configs
        
        mock_input1 = Mock()
        mock_input2 = Mock()
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation') as mock_get_comp:
                mock_get_comp.side_effect = [mock_input1, mock_input2]
                
                sum_comp = Sum.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        assert sum_comp.metadata == self.mock_metadata
        assert sum_comp.inputs == [mock_input1, mock_input2]
        assert mock_get_comp.call_count == 2
    
    def test_sum_compute(self):
        """Sum.compute should sum all input computations"""
        mock_input1 = Mock()
        mock_input2 = Mock()
        mock_input1.compute.return_value = 150.0
        mock_input2.compute.return_value = 250.0
        
        sum_comp = Sum(self.mock_metadata, [mock_input1, mock_input2])
        
        mock_context = Mock()
        mock_datum = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        mock_result = Mock()
        
        result = sum_comp.compute("session", date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should compute all inputs
        mock_input1.compute.assert_called_once()
        mock_input2.compute.assert_called_once()
        
        # Should sum results
        assert result == 400.0
        
        # Should store result
        mock_result.set.assert_called_once_with("sum-1", mock_datum)
    
    def test_sum_get_output(self):
        """Sum.get_output should return BreakdownResult with input outputs"""
        mock_input1 = Mock()
        mock_input2 = Mock()
        sum_comp = Sum(self.mock_metadata, [mock_input1, mock_input2])
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_output1 = Mock()
        mock_output2 = Mock()
        mock_input1.get_output.return_value = mock_output1
        mock_input2.get_output.return_value = mock_output2
        
        with patch('ixbrl_reporter.computation.BreakdownResult') as mock_breakdown_result:
            mock_breakdown_instance = Mock()
            mock_breakdown_result.return_value = mock_breakdown_instance
            
            output = sum_comp.get_output(mock_result)
        
        # Should get output from all inputs
        mock_input1.get_output.assert_called_once_with(mock_result)
        mock_input2.get_output.assert_called_once_with(mock_result)
        
        # Should create breakdown with all outputs
        mock_breakdown_result.assert_called_once_with(
            sum_comp, mock_datum, items=[mock_output1, mock_output2]
        )
        assert output == mock_breakdown_instance