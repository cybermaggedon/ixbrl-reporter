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
        """ResultSet.get should retrieve values"""
        rs = ResultSet()
        rs["existing"] = "value"
        
        assert rs.get("existing") == "value"


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
        
        def mock_get(key, deflt=None, mandatory=True):
            values = {
                "id": "test-id",
                "description": "Test Desc", 
                "period": "at-end",
                "segments": [],
                "note": None
            }
            return values.get(key, deflt)
        
        mock_cfg.get.side_effect = mock_get
        
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
        
        def mock_get(key, deflt=None, mandatory=True):
            values = {
                "id": None,
                "description": "Test Desc",
                "period": "at-end", 
                "segments": [],
                "note": None
            }
            return values.get(key, deflt)
        
        mock_cfg.get.side_effect = mock_get
        
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
            
            def mock_get(key, deflt=None, mandatory=True, period=period_str):
                values = {
                    "id": "test-id",
                    "description": "Test Desc",
                    "period": period,
                    "segments": [],
                    "note": None
                }
                return values.get(key, deflt)
            
            mock_cfg.get.side_effect = mock_get
            
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
        
        def mock_get(key, deflt=None, mandatory=True):
            values = {
                "id": "test-id",
                "description": "Test",
                "period": "at-end",
                "segments": segments_config,
                "note": None
            }
            return values.get(key, deflt)
        
        mock_cfg.get.side_effect = mock_get
        
        metadata = Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
        
        assert metadata.segments == [
            ("dimension1", "value1"),
            ("dimension2", "actual_value")
        ]
    
    def test_metadata_load_segments_validation_not_list(self):
        """Metadata.load should raise error if segments is not list"""
        mock_cfg = Mock()
        
        def mock_get(key, deflt=None, mandatory=True):
            values = {
                "id": "test-id",
                "description": "Test",
                "period": "at-end",
                "segments": "not-a-list",  # Invalid
                "note": None
            }
            return values.get(key, deflt)
        
        mock_cfg.get.side_effect = mock_get
        
        with pytest.raises(RuntimeError, match="segments should be list of single-item maps"):
            Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
    
    def test_metadata_load_segments_validation_multiple_items(self):
        """Metadata.load should raise error if segment has multiple items"""
        mock_cfg = Mock()
        segments_config = [
            {"dim1": "val1", "dim2": "val2"}  # Multiple items - invalid
        ]
        
        def mock_get(key, deflt=None, mandatory=True):
            values = {
                "id": "test-id",
                "description": "Test",
                "period": "at-end",
                "segments": segments_config,
                "note": None
            }
            return values.get(key, deflt)
        
        mock_cfg.get.side_effect = mock_get
        
        with pytest.raises(RuntimeError, match="segments should be list of single-item maps"):
            Metadata.load(mock_cfg, {}, self.mock_context, None, self.mock_gcfg)
    
    def test_metadata_load_with_note(self):
        """Metadata.load should handle note field"""
        mock_cfg = Mock()
        def mock_get(key, deflt=None, mandatory=True):
            values = {
                "id": "test-id",
                "description": "Test",
                "period": "at-end",
                "segments": [],
                "note": 12345  # Will be converted to string
            }
            return values.get(key, deflt)
        
        mock_cfg.get.side_effect = mock_get
        
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
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = constant.get_output(mock_result)
        
        mock_result.get.assert_called_once_with("const-1")
        mock_simple_result.assert_called_once_with(constant, mock_datum)
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
        """Group.get_output should return TotalResult for hidden breakdown"""
        mock_input = Mock()
        mock_input.get_output.return_value = Mock()
        
        group = Group(self.mock_metadata)
        group.add(mock_input)
        group.hide_breakdown = True
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        with patch('ixbrl_reporter.computation.TotalResult') as mock_total_result:
            with patch('ixbrl_reporter.computation.BreakdownResult') as mock_breakdown_result:
                mock_breakdown_instance = Mock()
                mock_breakdown_result.return_value = mock_breakdown_instance
                mock_total_instance = Mock()
                mock_total_result.return_value = mock_total_instance
                
                output = group.get_output(mock_result)
        
        # Should create hidden BreakdownResult first
        mock_breakdown_result.assert_called_once()
        # Should create TotalResult with BreakdownResult as item
        mock_total_result.assert_called_once_with(group, mock_datum, items=[mock_breakdown_instance])
        assert output == mock_total_instance
    
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
        """Sum should initialize with metadata and empty steps"""
        sum_comp = Sum(self.mock_metadata)
        
        assert sum_comp.metadata == self.mock_metadata
        assert sum_comp.steps == []
    
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
        assert sum_comp.steps == [mock_input1, mock_input2]
        assert mock_get_comp.call_count == 2
    
    def test_sum_compute(self):
        """Sum.compute should sum all input computations"""
        mock_input1 = Mock()
        mock_input2 = Mock()
        mock_input1.compute.return_value = 150.0
        mock_input2.compute.return_value = 250.0
        
        sum_comp = Sum(self.mock_metadata)
        sum_comp.add(mock_input1)
        sum_comp.add(mock_input2)
        
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
        """Sum.get_output should return TotalResult with input outputs"""
        mock_input1 = Mock()
        mock_input2 = Mock()
        sum_comp = Sum(self.mock_metadata)
        sum_comp.add(mock_input1)
        sum_comp.add(mock_input2)
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_output1 = Mock()
        mock_output2 = Mock()
        mock_input1.get_output.return_value = mock_output1
        mock_input2.get_output.return_value = mock_output2
        
        with patch('ixbrl_reporter.computation.TotalResult') as mock_total_result:
            mock_total_instance = Mock()
            mock_total_result.return_value = mock_total_instance
            
            output = sum_comp.get_output(mock_result)
        
        # Should get output from all inputs - Note: Sum doesn't call get_output on steps
        # It just returns the steps directly as items
        
        # Should create TotalResult with steps as items
        mock_total_result.assert_called_once_with(
            sum_comp, mock_datum, items=[mock_input1, mock_input2]
        )
        assert output == mock_total_instance


class TestAbsOperation:
    """Test AbsOperation computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "abs-1"
        self.mock_input = Mock()
    
    def test_abs_operation_init(self):
        """AbsOperation should initialize with metadata and input"""
        abs_op = AbsOperation(self.mock_metadata, self.mock_input)
        
        assert abs_op.metadata == self.mock_metadata
        assert abs_op.input == self.mock_input
    
    def test_abs_operation_load(self):
        """AbsOperation.load should create AbsOperation from config"""
        mock_cfg = Mock()
        mock_cfg.get.return_value = "input_ref"
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input) as mock_get_comp:
                abs_op = AbsOperation.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        mock_get_comp.assert_called_once_with("input_ref", "comps", "context", "data", "gcfg")
        assert abs_op.metadata == self.mock_metadata
        assert abs_op.input == self.mock_input
    
    def test_abs_operation_compute_positive(self):
        """AbsOperation.compute should return absolute value of positive input"""
        self.mock_input.compute.return_value = 150.0
        
        abs_op = AbsOperation(self.mock_metadata, self.mock_input)
        
        mock_context = Mock()
        mock_datum = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        mock_result = Mock()
        
        result = abs_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should compute input
        self.mock_input.compute.assert_called_once()
        
        # Should return absolute value (same for positive)
        assert result == 150.0
        
        # Should store result
        mock_context.create_money_datum.assert_called_once_with("abs-1", 150.0)
        mock_result.set.assert_called_once_with("abs-1", mock_datum)
    
    def test_abs_operation_compute_negative(self):
        """AbsOperation.compute should return absolute value of negative input"""
        self.mock_input.compute.return_value = -150.0
        
        abs_op = AbsOperation(self.mock_metadata, self.mock_input)
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        result = abs_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        # Should return absolute value
        assert result == 150.0
    
    def test_abs_operation_get_output(self):
        """AbsOperation.get_output should return SimpleResult with input output"""
        abs_op = AbsOperation(self.mock_metadata, self.mock_input)
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_input_output = Mock()
        self.mock_input.get_output.return_value = mock_input_output
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = abs_op.get_output(mock_result)
        
        # Should get output from input
        self.mock_input.get_output.assert_called_once_with(mock_result)
        
        # Should create simple result
        mock_simple_result.assert_called_once_with(abs_op, mock_datum, items=[mock_input_output])
        assert output == mock_simple_instance


class TestApportionOperation:
    """Test ApportionOperation computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "apportion-1"
        self.mock_input = Mock()
    
    def test_apportion_operation_init(self):
        """ApportionOperation should initialize with metadata, input and periods"""
        proportion_period = Mock()
        whole_period = Mock()
        
        apportion_op = ApportionOperation(
            self.mock_metadata, self.mock_input, proportion_period, whole_period
        )
        
        assert apportion_op.metadata == self.mock_metadata
        assert apportion_op.input == self.mock_input
        assert apportion_op.proportion_period == proportion_period
        assert apportion_op.whole_period == whole_period
    
    def test_apportion_operation_load(self):
        """ApportionOperation.load should create ApportionOperation from config"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key: {
            "input": "input_ref",
            "proportion": "2023-01-01/2023-03-31",
            "whole": "2023-01-01/2023-12-31"
        }[key]
        
        mock_proportion_period = Mock()
        mock_whole_period = Mock()
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                with patch('ixbrl_reporter.computation.Period') as mock_period_class:
                    mock_period_class.side_effect = [mock_proportion_period, mock_whole_period]
                    
                    apportion_op = ApportionOperation.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        # Should have created periods
        assert mock_period_class.call_count == 2
        assert apportion_op.proportion_period == mock_proportion_period
        assert apportion_op.whole_period == mock_whole_period
    
    def test_apportion_operation_compute(self):
        """ApportionOperation.compute should calculate proportional value"""
        # Set up periods
        mock_proportion_period = Mock()
        mock_whole_period = Mock()
        mock_proportion_period.days.return_value = 90  # 3 months
        mock_whole_period.days.return_value = 365      # 1 year
        
        # Set up input computation
        self.mock_input.compute.return_value = 1200.0  # Full year value
        
        apportion_op = ApportionOperation(
            self.mock_metadata, self.mock_input, mock_proportion_period, mock_whole_period
        )
        
        mock_context = Mock()
        mock_datum = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        mock_result = Mock()
        
        result = apportion_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should compute input
        self.mock_input.compute.assert_called_once()
        
        # Should calculate proportion: 1200 * (90/365)
        expected_result = 1200.0 * (90.0 / 365.0)
        assert abs(result - expected_result) < 0.01  # Allow for floating point precision
        
        # Should store result
        mock_result.set.assert_called_once_with("apportion-1", mock_datum)
    
    def test_apportion_operation_get_output(self):
        """ApportionOperation.get_output should return SimpleResult with input output"""
        apportion_op = ApportionOperation(self.mock_metadata, self.mock_input, Mock(), Mock())
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_input_output = Mock()
        self.mock_input.get_output.return_value = mock_input_output
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = apportion_op.get_output(mock_result)
        
        # Should get output from input
        self.mock_input.get_output.assert_called_once_with(mock_result)
        
        # Should create simple result
        mock_simple_result.assert_called_once_with(apportion_op, mock_datum, items=[mock_input_output])
        assert output == mock_simple_instance


class TestRoundOperation:
    """Test RoundOperation computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "round-1"
        self.mock_input = Mock()
    
    def test_round_operation_init(self):
        """RoundOperation should initialize with metadata, input and direction"""
        round_op = RoundOperation(self.mock_metadata, self.mock_input, ROUND_UP)
        
        assert round_op.metadata == self.mock_metadata
        assert round_op.input == self.mock_input
        assert round_op.direction == ROUND_UP
    
    def test_round_operation_load(self):
        """RoundOperation.load should create RoundOperation from config"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key: {
            "input": "input_ref",
            "direction": "up"
        }[key]
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                round_op = RoundOperation.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        assert round_op.direction == ROUND_UP
    
    def test_round_operation_load_directions(self):
        """RoundOperation.load should handle all rounding directions"""
        test_cases = [
            ("up", ROUND_UP),
            ("down", ROUND_DOWN),
            ("nearest", ROUND_NEAREST),
            ("invalid", ROUND_NEAREST)  # Default fallback
        ]
        
        for direction_str, expected_const in test_cases:
            mock_cfg = Mock()
            mock_cfg.get.side_effect = lambda key: {
                "input": "input_ref",
                "direction": direction_str
            }[key]
            
            with patch.object(Metadata, 'load', return_value=self.mock_metadata):
                with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                    round_op = RoundOperation.load(mock_cfg, "comps", "context", "data", "gcfg")
            
            assert round_op.direction == expected_const
    
    def test_round_operation_compute_round_up(self):
        """RoundOperation.compute should round up correctly"""
        self.mock_input.compute.return_value = 123.45
        
        round_op = RoundOperation(self.mock_metadata, self.mock_input, ROUND_UP)
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        with patch('math.ceil', return_value=124) as mock_ceil:
            result = round_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        mock_ceil.assert_called_once_with(123.45)
        assert result == 124
    
    def test_round_operation_compute_round_down(self):
        """RoundOperation.compute should round down correctly"""
        self.mock_input.compute.return_value = 123.45
        
        round_op = RoundOperation(self.mock_metadata, self.mock_input, ROUND_DOWN)
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        with patch('math.floor', return_value=123) as mock_floor:
            result = round_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        mock_floor.assert_called_once_with(123.45)
        assert result == 123
    
    def test_round_operation_compute_round_nearest(self):
        """RoundOperation.compute should round to nearest correctly"""
        self.mock_input.compute.return_value = 123.45
        
        round_op = RoundOperation(self.mock_metadata, self.mock_input, ROUND_NEAREST)
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        result = round_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        # Should use Python's built-in round function
        assert result == round(123.45)  # 123
    
    def test_round_operation_get_output(self):
        """RoundOperation.get_output should return SimpleResult with input output"""
        round_op = RoundOperation(self.mock_metadata, self.mock_input, ROUND_NEAREST)
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_input_output = Mock()
        self.mock_input.get_output.return_value = mock_input_output
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = round_op.get_output(mock_result)
        
        # Should get output from input
        self.mock_input.get_output.assert_called_once_with(mock_result)
        
        # Should create simple result
        mock_simple_result.assert_called_once_with(round_op, mock_datum, items=[mock_input_output])
        assert output == mock_simple_instance


class TestFactorOperation:
    """Test FactorOperation computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "factor-1"
        self.mock_input = Mock()
    
    def test_factor_operation_init_with_static_factor(self):
        """FactorOperation should initialize with static factor"""
        factor_op = FactorOperation(self.mock_metadata, self.mock_input, 1.5)
        
        assert factor_op.metadata == self.mock_metadata
        assert factor_op.item == self.mock_input
        assert factor_op.factor == 1.5
    
    def test_factor_operation_init_with_factor_map(self):
        """FactorOperation should initialize with factor map"""
        factors = {"2023-12-31": 1.2, "2024-12-31": 1.3}
        factor_op = FactorOperation(self.mock_metadata, self.mock_input, factors)
        
        assert factor_op.factor == factors
    
    def test_factor_operation_load_static_factor(self):
        """FactorOperation.load should create FactorOperation with static factor"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, deflt=None, mandatory=True: {
            "input": "input_ref",
            "factor": 2.0
        }.get(key, deflt)
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                factor_op = FactorOperation.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        assert factor_op.factor == 2.0
    
    def test_factor_operation_load_factor_map(self):
        """FactorOperation.load should create FactorOperation with factor map"""
        factors = {"2023-12-31": 1.5}
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, deflt=None, mandatory=True: {
            "input": "input_ref",
            "factor": factors
        }.get(key, deflt)
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                factor_op = FactorOperation.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        assert factor_op.factor == factors
    
    def test_factor_operation_compute_static_factor(self):
        """FactorOperation.compute should multiply by static factor"""
        self.mock_input.compute.return_value = 100.0
        
        factor_op = FactorOperation(self.mock_metadata, self.mock_input, 1.5)
        
        mock_context = Mock()
        mock_datum = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        mock_result = Mock()
        
        result = factor_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should compute input
        self.mock_input.compute.assert_called_once()
        
        # Should multiply by factor
        assert result == 150.0  # 100.0 * 1.5
        
        # Should store result
        mock_context.create_money_datum.assert_called_once_with("factor-1", 150.0)
        mock_result.set.assert_called_once_with("factor-1", mock_datum)
    
    def test_factor_operation_compute_factor_map(self):
        """FactorOperation.compute should use factor from map based on end date"""
        self.mock_input.compute.return_value = 200.0
        factors = {"2023-12-31": 1.2, "2024-12-31": 1.8}
        
        factor_op = FactorOperation(self.mock_metadata, self.mock_input, factors)
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        result = factor_op.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        # Should use factor for 2023-12-31
        assert result == 240.0  # 200.0 * 1.2
    
    def test_factor_operation_get_output(self):
        """FactorOperation.get_output should return SimpleResult with input output"""
        factor_op = FactorOperation(self.mock_metadata, self.mock_input, 1.0)
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_input_output = Mock()
        self.mock_input.get_output.return_value = mock_input_output
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = factor_op.get_output(mock_result)
        
        # Should get output from input
        self.mock_input.get_output.assert_called_once_with(mock_result)
        
        # Should create simple result
        mock_simple_result.assert_called_once_with(factor_op, mock_datum, items=[mock_input_output])
        assert output == mock_simple_instance


class TestComparison:
    """Test Comparison computation class"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.mock_metadata = Mock()
        self.mock_metadata.id = "compare-1"
        self.mock_input = Mock()
    
    def test_comparison_init(self):
        """Comparison should initialize with all parameters"""
        comparison = Comparison(
            self.mock_metadata, self.mock_input, CMP_GREATER, 100.0, 0.0
        )
        
        assert comparison.metadata == self.mock_metadata
        assert comparison.item == self.mock_input
        assert comparison.comparison == CMP_GREATER
        assert comparison.value == 100.0
        assert comparison.false_value == 0.0
    
    def test_comparison_load(self):
        """Comparison.load should create Comparison from config"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = lambda key, deflt=None, mandatory=True: {
            "input": "input_ref",
            "comparison": "greater",
            "value": 50.0,
            "if-false": 0.0
        }.get(key, deflt)
        
        with patch.object(Metadata, 'load', return_value=self.mock_metadata):
            with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                comparison = Comparison.load(mock_cfg, "comps", "context", "data", "gcfg")
        
        assert comparison.comparison == CMP_GREATER
        assert comparison.value == 50.0
        assert comparison.false_value == 0.0
    
    def test_comparison_load_all_operations(self):
        """Comparison.load should handle all comparison operations"""
        test_cases = [
            ("less", CMP_LESS),
            ("less-equal", CMP_LESS_EQUAL),
            ("greater", CMP_GREATER),
            ("greater-equal", CMP_GREATER_EQUAL),
            ("invalid", CMP_LESS)  # Default fallback
        ]
        
        for op_str, expected_const in test_cases:
            mock_cfg = Mock()
            def mock_get(key, deflt=None, mandatory=True, op=op_str):
                values = {
                    "input": "input_ref",
                    "comparison": op,
                    "value": 100.0,
                    "if-false": 0.0
                }
                return values.get(key, deflt)
            
            mock_cfg.get.side_effect = mock_get
            
            with patch.object(Metadata, 'load', return_value=self.mock_metadata):
                with patch('ixbrl_reporter.computation.get_computation', return_value=self.mock_input):
                    comparison = Comparison.load(mock_cfg, "comps", "context", "data", "gcfg")
            
            assert comparison.comparison == expected_const
    
    def test_comparison_compute_greater_true(self):
        """Comparison.compute should return input value when comparison is true (greater)"""
        self.mock_input.compute.return_value = 150.0
        
        comparison = Comparison(self.mock_metadata, self.mock_input, CMP_GREATER, 100.0, 0.0)
        
        mock_context = Mock()
        mock_datum = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        mock_context.create_money_datum.return_value = mock_datum
        
        mock_result = Mock()
        
        result = comparison.compute("session", date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should compute input
        self.mock_input.compute.assert_called_once()
        
        # 150 > 100, so should return input value
        assert result == 150.0
        
        # Should store result
        mock_context.create_money_datum.assert_called_once_with("compare-1", 150.0)
        mock_result.set.assert_called_once_with("compare-1", mock_datum)
    
    def test_comparison_compute_greater_false(self):
        """Comparison.compute should return false_value when comparison is false (greater)"""
        self.mock_input.compute.return_value = 50.0
        
        comparison = Comparison(self.mock_metadata, self.mock_input, CMP_GREATER, 100.0, -1.0)
        
        mock_context = Mock()
        self.mock_metadata.get_context.return_value = mock_context
        
        result = comparison.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
        
        # 50 > 100 is false, so should return false_value
        assert result == -1.0
    
    def test_comparison_compute_all_operations(self):
        """Comparison.compute should handle all comparison operations correctly"""
        test_cases = [
            (CMP_LESS, 50.0, 100.0, True),          # 50 < 100
            (CMP_LESS, 150.0, 100.0, False),        # 150 < 100
            (CMP_LESS_EQUAL, 100.0, 100.0, True),   # 100 <= 100
            (CMP_LESS_EQUAL, 150.0, 100.0, False),  # 150 <= 100
            (CMP_GREATER, 150.0, 100.0, True),      # 150 > 100
            (CMP_GREATER, 50.0, 100.0, False),      # 50 > 100
            (CMP_GREATER_EQUAL, 100.0, 100.0, True), # 100 >= 100
            (CMP_GREATER_EQUAL, 50.0, 100.0, False), # 50 >= 100
        ]
        
        for op, input_val, compare_val, should_be_true in test_cases:
            self.mock_input.compute.return_value = input_val
            
            comparison = Comparison(self.mock_metadata, self.mock_input, op, compare_val, -999.0)
            
            mock_context = Mock()
            self.mock_metadata.get_context.return_value = mock_context
            
            result = comparison.compute("session", date(2023, 1, 1), date(2023, 12, 31), Mock())
            
            if should_be_true:
                assert result == input_val, f"Op {op}: {input_val} vs {compare_val} should return input"
            else:
                assert result == -999.0, f"Op {op}: {input_val} vs {compare_val} should return false_value"
    
    def test_comparison_get_output(self):
        """Comparison.get_output should return SimpleResult with input output"""
        comparison = Comparison(self.mock_metadata, self.mock_input, CMP_GREATER, 100.0, 0.0)
        
        mock_result = Mock()
        mock_datum = Mock()
        mock_result.get.return_value = mock_datum
        
        mock_input_output = Mock()
        self.mock_input.get_output.return_value = mock_input_output
        
        with patch('ixbrl_reporter.computation.SimpleResult') as mock_simple_result:
            mock_simple_instance = Mock()
            mock_simple_result.return_value = mock_simple_instance
            
            output = comparison.get_output(mock_result)
        
        # Should get output from input
        self.mock_input.get_output.assert_called_once_with(mock_result)
        
        # Should create simple result
        mock_simple_result.assert_called_once_with(comparison, mock_datum, items=[mock_input_output])
        assert output == mock_simple_instance


class TestIntegration:
    """Integration tests for computation module"""
    
    def test_complex_computation_workflow(self):
        """Test complete workflow with nested computations"""
        # Create a complex computation: Group(Sum(Line1, Line2), AbsOperation(Line3))
        
        # Set up metadata
        mock_metadata = Mock()
        mock_metadata.id = "complex-comp"
        mock_metadata.get_context.return_value = Mock()
        
        # Set up line computations
        mock_line1 = Mock()
        mock_line1.compute.return_value = 100.0
        
        mock_line2 = Mock()
        mock_line2.compute.return_value = 200.0
        
        mock_line3 = Mock()
        mock_line3.compute.return_value = -50.0
        
        # Create sum of line1 and line2
        mock_sum_metadata = Mock()
        mock_sum_metadata.get_context.return_value = Mock()
        sum_comp = Sum(mock_sum_metadata)
        sum_comp.add(mock_line1)
        sum_comp.add(mock_line2)
        
        # Create abs of line3
        mock_abs_metadata = Mock()
        mock_abs_metadata.get_context.return_value = Mock()
        abs_comp = AbsOperation(mock_abs_metadata, mock_line3)
        
        # Create group of sum and abs
        group = Group(mock_metadata)
        group.add(sum_comp)
        group.add(abs_comp)
        
        # Execute computation
        mock_result = Mock()
        
        result = group.compute("session", date(2023, 1, 1), date(2023, 12, 31), mock_result)
        
        # Should compute: (100 + 200) + abs(-50) = 300 + 50 = 350
        assert result == 350.0
        
        # Verify all components were computed
        mock_line1.compute.assert_called_once()
        mock_line2.compute.assert_called_once()
        mock_line3.compute.assert_called_once()
    
    def test_get_computations_function(self):
        """Test get_computations function loads all computations from config"""
        computations_data = [
            {
                "kind": "line",
                "accounts": ["Assets:Bank"],
                "description": "Bank balance"
            },
            {
                "kind": "sum",
                "inputs": ["line1"],
                "description": "Total assets"
            }
        ]
        
        mock_context = Mock()
        mock_data = Mock()
        mock_gcfg = Mock()
        mock_gcfg.get.return_value = computations_data
        
        with patch('ixbrl_reporter.computation.Computable.load') as mock_load:
            mock_comp1 = Mock()
            mock_comp1.metadata.id = "comp1"
            mock_comp2 = Mock()
            mock_comp2.metadata.id = "comp2"
            mock_load.side_effect = [mock_comp1, mock_comp2]
            
            from ixbrl_reporter.computation import get_computations
            result = get_computations(mock_gcfg, mock_context, mock_data)
        
        # Should have created computations for both items
        assert mock_load.call_count == 2
        
        # Should call gcfg.get for "report.computations"
        mock_gcfg.get.assert_called_once_with("report.computations")
        
        # Should return dictionary of computations by id
        assert "comp1" in result
        assert "comp2" in result
        assert result["comp1"] == mock_comp1
        assert result["comp2"] == mock_comp2