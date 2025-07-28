"""
Unit tests for data_source module

The data_source module is the central data orchestration component that coordinates
accounts, computations, configuration, and reporting functionality.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date

from ixbrl_reporter.data_source import DataSource, NoteHeadings
from ixbrl_reporter.datum import StringDatum, DateDatum, MoneyDatum, BoolDatum, NumberDatum, VariableDatum
from ixbrl_reporter.period import Period
from ixbrl_reporter.context import Context
from ixbrl_reporter.config import NoneValue
from ixbrl_reporter.valueset import ValueSet
from ixbrl_reporter.computation import ResultSet


class TestNoteHeadings:
    """Test the NoteHeadings class for managing note section numbering"""
    
    def test_init(self):
        """Test NoteHeadings initialization"""
        headings = NoteHeadings()
        assert isinstance(headings, dict)
        assert len(headings) == 0
    
    def test_maybe_init_new_level(self):
        """Test maybe_init with new level"""
        headings = NoteHeadings()
        headings.maybe_init(1)
        assert headings[1] == 1
    
    def test_maybe_init_existing_level(self):
        """Test maybe_init with existing level doesn't overwrite"""
        headings = NoteHeadings()
        headings[1] = 5
        headings.maybe_init(1)
        assert headings[1] == 5
    
    def test_get_next_new_level(self):
        """Test get_next with new level"""
        headings = NoteHeadings()
        result = headings.get_next(1)
        assert result == 1
        assert headings[1] == 2
    
    def test_get_next_existing_level(self):
        """Test get_next with existing level increments"""
        headings = NoteHeadings()
        headings[2] = 3
        result = headings.get_next(2)
        assert result == 3
        assert headings[2] == 4
    
    def test_get_next_level_1_deletes_level_2(self):
        """Test that getting next level 1 deletes level 2"""
        headings = NoteHeadings()
        headings[1] = 2
        headings[2] = 5
        
        result = headings.get_next(1)
        
        assert result == 2
        assert headings[1] == 3
        assert 2 not in headings
    
    def test_get_next_level_1_no_level_2_doesnt_error(self):
        """Test that getting next level 1 when no level 2 doesn't error"""
        headings = NoteHeadings()
        
        result = headings.get_next(1)
        
        assert result == 1
        assert headings[1] == 2


class TestDataSource:
    """Test the DataSource class"""
    
    def test_init_basic(self):
        """Test basic DataSource initialization"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "http://www.companieshouse.gov.uk/",  # entity-scheme
            "12345678"  # company-number
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations') as mock_get_computations, \
             patch('ixbrl_reporter.data_source.Context') as mock_context_class:
            
            mock_root_context = Mock()
            mock_business_context = Mock()
            mock_context_class.return_value = mock_root_context
            mock_root_context.with_entity.return_value = mock_business_context
            
            mock_computations = {"comp1": Mock()}
            mock_get_computations.return_value = mock_computations
            
            data_source = DataSource(mock_cfg, mock_session)
            
            assert data_source.cfg == mock_cfg
            assert data_source.session == mock_session
            assert data_source.root_context == mock_root_context
            assert data_source.business_context == mock_business_context
            assert data_source.computations == mock_computations
            assert isinstance(data_source.results, dict)
            assert isinstance(data_source.notes, dict)
            assert isinstance(data_source.noteheadings, NoteHeadings)
            
            mock_cfg.get.assert_any_call("metadata.business.entity-scheme")
            mock_cfg.get.assert_any_call("metadata.business.company-number")
            mock_root_context.with_entity.assert_called_once_with(
                "http://www.companieshouse.gov.uk/", "12345678"
            )
    
    def test_set_note(self):
        """Test setting a note"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            data_source.set_note("note1", "Note content")
            
            assert data_source.notes["note1"] == "Note content"
    
    def test_get_note(self):
        """Test getting a note"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            data_source.notes["note1"] = "Note content"
            
            result = data_source.get_note("note1")
            assert result == "Note content"
    
    def test_expand_string(self):
        """Test string expansion"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.expand_string') as mock_expand:
            
            mock_expand.return_value = "expanded string"
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.expand_string("template string")
            
            mock_expand.assert_called_once_with("template string", data_source)
            assert result == "expanded string"
    
    def test_get_business_context(self):
        """Test getting business context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            mock_business_context = Mock()
            data_source.business_context = mock_business_context
            
            result = data_source.get_business_context()
            assert result == mock_business_context
    
    def test_get_root_context(self):
        """Test getting root context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            mock_root_context = Mock()
            data_source.root_context = mock_root_context
            
            result = data_source.get_root_context()
            assert result == mock_root_context
    
    def test_get_report_period(self):
        """Test getting report period"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"}  # period
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.Period.load') as mock_period_load:
            
            mock_period = Mock()
            mock_period_load.return_value = mock_period
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_report_period(0)
            
            mock_cfg.get.assert_called_with("metadata.accounting.periods.0")
            mock_period_load.assert_called_once_with(
                {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"}
            )
            assert result == mock_period
    
    def test_get_report_period_with_index(self):
        """Test getting report period with specific index"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            {"name": "2019", "start": "2019-01-01", "end": "2019-12-31"}  # period
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.Period.load') as mock_period_load:
            
            mock_period = Mock()
            mock_period_load.return_value = mock_period
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_report_period(1)
            
            mock_cfg.get.assert_called_with("metadata.accounting.periods.1")
            assert result == mock_period
    
    def test_get_report_date(self):
        """Test getting report date"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_cfg.get_date.return_value = date(2020, 12, 31)
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_report_date()
            
            mock_cfg.get_date.assert_called_once_with("metadata.accounting.date")
            assert result == date(2020, 12, 31)
    
    def test_get_computation_existing(self):
        """Test getting existing computation"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            mock_computation = Mock()
            data_source.computations["test-comp"] = mock_computation
            
            result = data_source.get_computation("test-comp")
            assert result == mock_computation
    
    def test_get_computation_nonexistent_raises_error(self):
        """Test getting nonexistent computation raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with pytest.raises(RuntimeError, match="No such computation 'nonexistent'"):
                data_source.get_computation("nonexistent")
    
    def test_perform_computations_new_context(self):
        """Test performing computations for new context"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.ResultSet') as mock_result_set_class:
            
            mock_business_context = Mock()
            mock_context_with_period = Mock()
            mock_business_context.with_period.return_value = mock_context_with_period
            
            mock_period = Mock()
            mock_period.start = date(2020, 1, 1)
            mock_period.end = date(2020, 12, 31)
            
            mock_computation1 = Mock()
            mock_computation2 = Mock()
            mock_computations = {
                "comp1": mock_computation1,
                "comp2": mock_computation2
            }
            
            mock_result_set = Mock()
            mock_result_set_class.return_value = mock_result_set
            
            data_source = DataSource(mock_cfg, mock_session)
            data_source.business_context = mock_business_context
            data_source.computations = mock_computations
            
            result = data_source.perform_computations(mock_period)
            
            mock_business_context.with_period.assert_called_once_with(mock_period)
            mock_computation1.compute.assert_called_once_with(
                mock_session, date(2020, 1, 1), date(2020, 12, 31), mock_result_set
            )
            mock_computation2.compute.assert_called_once_with(
                mock_session, date(2020, 1, 1), date(2020, 12, 31), mock_result_set
            )
            assert data_source.results[mock_context_with_period] == mock_result_set
            assert result == mock_result_set
    
    def test_perform_computations_existing_context(self):
        """Test performing computations for existing context returns cached result"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            mock_business_context = Mock()
            mock_context_with_period = Mock()
            mock_business_context.with_period.return_value = mock_context_with_period
            
            mock_period = Mock()
            mock_existing_result = Mock()
            
            data_source = DataSource(mock_cfg, mock_session)
            data_source.business_context = mock_business_context
            data_source.results[mock_context_with_period] = mock_existing_result
            
            result = data_source.perform_computations(mock_period)
            
            assert result == mock_existing_result
    
    def test_get_result(self):
        """Test getting single result"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            mock_period = Mock()
            mock_valueset = Mock()
            mock_datum = Mock()
            mock_valueset.get.return_value = mock_datum
            
            with patch.object(data_source, 'get_results', return_value=mock_valueset) as mock_get_results:
                result = data_source.get_result("test-id", mock_period)
                
                mock_get_results.assert_called_once_with(["test-id"], mock_period)
                mock_valueset.get.assert_called_once_with("test-id")
                assert result == mock_datum
    
    def test_get_results(self):
        """Test getting multiple results"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.ValueSet') as mock_value_set_class:
            
            mock_period = Mock()
            mock_result_set = Mock()
            mock_datum1 = Mock()
            mock_datum2 = Mock()
            mock_result_set.get.side_effect = [mock_datum1, mock_datum2]
            
            mock_value_set = Mock()
            mock_value_set_class.return_value = mock_value_set
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with patch.object(data_source, 'perform_computations', return_value=mock_result_set) as mock_perform:
                result = data_source.get_results(["id1", "id2"], mock_period)
                
                mock_perform.assert_called_once_with(mock_period)
                mock_result_set.get.assert_any_call("id1")
                mock_result_set.get.assert_any_call("id2")
                mock_value_set.add_datum.assert_any_call(mock_datum1)
                mock_value_set.add_datum.assert_any_call(mock_datum2)
                assert result == mock_value_set
    
    def test_get_periods(self):
        """Test getting all periods"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # periods
                {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"},
                {"name": "2019", "start": "2019-01-01", "end": "2019-12-31"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.Period.load') as mock_period_load:
            
            mock_period1 = Mock()
            mock_period2 = Mock()
            mock_period_load.side_effect = [mock_period1, mock_period2]
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_periods()
            
            mock_cfg.get.assert_called_with("metadata.accounting.periods")
            assert len(result) == 2
            assert result[0] == mock_period1
            assert result[1] == mock_period2
    
    def test_get_period_by_name_existing(self):
        """Test getting period by name"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            mock_period1 = Mock()
            mock_period1.name = "2020"
            mock_period2 = Mock()
            mock_period2.name = "2019"
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with patch.object(data_source, 'get_periods', return_value=[mock_period1, mock_period2]):
                result = data_source.get_period("2019")
                assert result == mock_period2
    
    def test_get_period_by_name_nonexistent_raises_error(self):
        """Test getting nonexistent period by name raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            mock_period = Mock()
            mock_period.name = "2020"
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with patch.object(data_source, 'get_periods', return_value=[mock_period]):
                with pytest.raises(RuntimeError, match="Period '.*' not known"):
                    data_source.get_period("nonexistent")
    
    def test_get_worksheet_simple(self):
        """Test getting simple worksheet"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # worksheets
                {"id": "ws1", "kind": "simple", "data": "test"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.SimpleWorksheet') as mock_simple_ws:
            
            mock_worksheet = Mock()
            mock_simple_ws.load.return_value = mock_worksheet
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_worksheet("ws1")
            
            mock_cfg.get.assert_called_with("report.worksheets")
            mock_simple_ws.load.assert_called_once_with(
                {"id": "ws1", "kind": "simple", "data": "test"}, data_source
            )
            assert result == mock_worksheet
    
    def test_get_worksheet_flex(self):
        """Test getting flex worksheet"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # worksheets
                {"id": "ws1", "kind": "flex", "data": "test"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.FlexWorksheet') as mock_flex_ws:
            
            mock_worksheet = Mock()
            mock_flex_ws.load.return_value = mock_worksheet
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_worksheet("ws1")
            
            mock_flex_ws.load.assert_called_once_with(
                {"id": "ws1", "kind": "flex", "data": "test"}, data_source
            )
            assert result == mock_worksheet
    
    def test_get_worksheet_unknown_kind_raises_error(self):
        """Test getting worksheet with unknown kind raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # worksheets
                {"id": "ws1", "kind": "unknown", "data": "test"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with pytest.raises(RuntimeError, match="Don't know worksheet type 'unknown'"):
                data_source.get_worksheet("ws1")
    
    def test_get_worksheet_nonexistent_raises_error(self):
        """Test getting nonexistent worksheet raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # worksheets
                {"id": "ws1", "kind": "simple", "data": "test"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with pytest.raises(RuntimeError, match="Could not find worksheet 'nonexistent'"):
                data_source.get_worksheet("nonexistent")
    
    def test_get_element_inline_dict(self):
        """Test getting element with inline dict definition"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.Element') as mock_element_class:
            
            mock_element = Mock()
            mock_element_class.load.return_value = mock_element
            
            data_source = DataSource(mock_cfg, mock_session)
            element_def = {"kind": "test", "id": "elem1"}
            result = data_source.get_element(element_def)
            
            mock_element_class.load.assert_called_once_with(element_def, data_source)
            assert result == mock_element
    
    def test_get_element_by_reference(self):
        """Test getting element by string reference"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # elements
                {"id": "elem1", "kind": "test", "data": "test"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'), \
             patch('ixbrl_reporter.data_source.Element') as mock_element_class:
            
            mock_element = Mock()
            mock_element_class.load.return_value = mock_element
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_element("elem1")
            
            mock_cfg.get.assert_called_with("report.elements")
            mock_element_class.load.assert_called_once_with(
                {"id": "elem1", "kind": "test", "data": "test"}, data_source
            )
            assert result == mock_element
    
    def test_get_element_no_elements_config_raises_error(self):
        """Test getting element when no elements config raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            Exception("Config not found")  # elements
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with pytest.raises(RuntimeError, match="Couldn't find report.elements"):
                data_source.get_element("elem1")
    
    def test_get_element_nonexistent_reference_raises_error(self):
        """Test getting nonexistent element by reference raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            [  # elements
                {"id": "elem1", "kind": "test", "data": "test"}
            ]
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with pytest.raises(RuntimeError, match="Could not find element 'nonexistent'"):
                data_source.get_element("nonexistent")
    
    def test_get_element_exception_during_search_raises_error(self):
        """Test getting element when exception during search raises error"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = [
            "scheme", "number",  # init
            Exception("Search error")  # elements config fails
        ]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            
            with pytest.raises(RuntimeError, match="Couldn't find report.elements"):
                data_source.get_element("elem1")
    
    def test_get_config(self):
        """Test getting config value"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_cfg.get.return_value = "config_value"
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            # Reset mock after init calls
            mock_cfg.reset_mock()
            mock_cfg.get.return_value = "config_value"
            
            result = data_source.get_config("test.key", "default", False)
            
            mock_cfg.get.assert_called_once_with("test.key", "default", False)
            assert result == "config_value"
    
    def test_get_config_date(self):
        """Test getting config date value"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_cfg.get_date.return_value = date(2020, 1, 1)
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_config_date("test.date", None, True)
            
            mock_cfg.get_date.assert_called_once_with("test.date", None, True)
            assert result == date(2020, 1, 1)
    
    def test_get_config_bool(self):
        """Test getting config boolean value"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_cfg.get_bool.return_value = True
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            data_source = DataSource(mock_cfg, mock_session)
            result = data_source.get_config_bool("test.bool", False, True)
            
            mock_cfg.get_bool.assert_called_once_with("test.bool", False, True)
            assert result == True


class TestDataSourceToDatum:
    """Test the to_datum method for converting definitions to datum objects"""
    
    def setup_method(self):
        """Set up basic DataSource for each test"""
        mock_cfg = Mock()
        mock_cfg.get.side_effect = ["scheme", "number"]
        mock_session = Mock()
        
        with patch('ixbrl_reporter.data_source.get_computations'), \
             patch('ixbrl_reporter.data_source.Context'):
            
            self.data_source = DataSource(mock_cfg, mock_session)
            self.mock_context = Mock()
    
    def test_to_datum_config_kind(self):
        """Test converting config kind definition to StringDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["config", "test-id", "config.key"]
        
        with patch.object(self.data_source, 'get_config', return_value="config_value") as mock_get_config:
            result = self.data_source.to_datum(mock_defn, self.mock_context)
            
            mock_get_config.assert_called_once_with("config.key")
            assert isinstance(result, StringDatum)
            assert result.id == "test-id"
            assert result.value == "config_value"
            assert result.context == self.mock_context
    
    def test_to_datum_config_date_kind(self):
        """Test converting config-date kind definition to DateDatum"""
        mock_defn = Mock()
        mock_defn.get.return_value = "config-date"  # Always return this kind
        mock_defn.get.side_effect = lambda key: {
            "kind": "config-date",
            "id": "test-id", 
            "key": "config.date"
        }.get(key)
        
        with patch.object(self.data_source, 'get_config_date', return_value=date(2020, 1, 1)) as mock_get_date:
            result = self.data_source.to_datum(mock_defn, self.mock_context)
            
            mock_get_date.assert_called_once_with("config.date")
            assert isinstance(result, DateDatum)
            assert result.id == "test-id"
            assert result.value == date(2020, 1, 1)
            assert result.context == self.mock_context
    
    def test_to_datum_config_bool_kind(self):
        """Test converting config-bool kind definition to BoolDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["config-bool", "test-id", "config.bool"]
        
        with patch.object(self.data_source, 'get_config_bool', return_value=True) as mock_get_bool:
            result = self.data_source.to_datum(mock_defn, self.mock_context)
            
            mock_get_bool.assert_called_once_with("config.bool")
            assert isinstance(result, BoolDatum)
            assert result.id == "test-id"
            assert result.value == True
            assert result.context == self.mock_context
    
    def test_to_datum_bool_kind(self):
        """Test converting bool kind definition to BoolDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["bool", "test-id"]
        mock_defn.get_bool.return_value = False
        
        result = self.data_source.to_datum(mock_defn, self.mock_context)
        
        mock_defn.get_bool.assert_called_once_with("value")
        assert isinstance(result, BoolDatum)
        assert result.id == "test-id"
        assert result.value == False
        assert result.context == self.mock_context
    
    def test_to_datum_string_kind(self):
        """Test converting string kind definition to StringDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["string", "test-id", "string_value"]
        
        result = self.data_source.to_datum(mock_defn, self.mock_context)
        
        assert isinstance(result, StringDatum)
        assert result.id == "test-id"
        assert result.value == "string_value"
        assert result.context == self.mock_context
    
    def test_to_datum_money_kind(self):
        """Test converting money kind definition to MoneyDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["money", "test-id", 1000.0]
        
        result = self.data_source.to_datum(mock_defn, self.mock_context)
        
        assert isinstance(result, MoneyDatum)
        assert result.id == "test-id"
        assert result.value == 1000.0
        assert result.context == self.mock_context
    
    def test_to_datum_number_kind(self):
        """Test converting number kind definition to NumberDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["number", "test-id", 3.14]
        
        result = self.data_source.to_datum(mock_defn, self.mock_context)
        
        assert isinstance(result, NumberDatum)
        assert result.id == "test-id"
        assert result.value == 3.14
        assert result.context == self.mock_context
    
    def test_to_datum_computation_kind(self):
        """Test converting computation kind definition"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["computation", "comp-id", "period.config"]
        
        mock_period_config = {"name": "2020", "start": "2020-01-01", "end": "2020-12-31"}
        mock_period = Mock()
        mock_value = Mock()
        mock_valueset = Mock()
        mock_valueset.get.return_value = mock_value
        
        with patch.object(self.data_source, 'get_config', return_value=mock_period_config) as mock_get_config, \
             patch('ixbrl_reporter.data_source.Period.load', return_value=mock_period) as mock_period_load, \
             patch.object(self.data_source, 'get_results', return_value=mock_valueset) as mock_get_results:
            
            result = self.data_source.to_datum(mock_defn, self.mock_context)
            
            mock_get_config.assert_called_once_with("period.config")
            mock_period_load.assert_called_once_with(mock_period_config)
            mock_get_results.assert_called_once_with(["comp-id"], mock_period)
            mock_valueset.get.assert_called_once_with("comp-id")
            assert result == mock_value
    
    def test_to_datum_variable_kind(self):
        """Test converting variable kind definition to VariableDatum"""
        mock_defn = Mock()
        mock_defn.get.side_effect = ["variable", "var-name"]
        
        result = self.data_source.to_datum(mock_defn, self.mock_context)
        
        assert isinstance(result, VariableDatum)
        assert result.id is None
        assert result.value == "var-name"
        assert result.context == self.mock_context
    
    def test_to_datum_unknown_kind_returns_none(self):
        """Test converting unknown kind definition returns None"""
        mock_defn = Mock()
        mock_defn.get.return_value = "unknown-kind"
        
        result = self.data_source.to_datum(mock_defn, self.mock_context)
        
        assert result is None