"""
Unit tests for ixbrl_reporter.ixbrl_reporter module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import date

from ixbrl_reporter.ixbrl_reporter import IxbrlReporter


class TestIxbrlReporterInit:
    """Test IxbrlReporter initialization"""
    
    def test_init_with_hide_notes_true(self):
        """IxbrlReporter should initialize with hide_notes flag"""
        reporter = IxbrlReporter(hide_notes=True)
        assert reporter.hide_notes is True
    
    def test_init_with_hide_notes_false(self):
        """IxbrlReporter should initialize with hide_notes flag"""
        reporter = IxbrlReporter(hide_notes=False)
        assert reporter.hide_notes is False


class TestIxbrlReporterTableOperations:
    """Test table creation and manipulation methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        self.mock_par = Mock()
        self.mock_xhtml_maker = Mock()
        self.mock_par.xhtml_maker = self.mock_xhtml_maker
        self.reporter.par = self.mock_par
    
    def test_create_table(self):
        """create_table should create HTML table with correct class"""
        mock_table = Mock()
        self.mock_xhtml_maker.table.return_value = mock_table
        
        result = self.reporter.create_table()
        
        self.mock_xhtml_maker.table.assert_called_once()
        mock_table.set.assert_called_once_with("class", "sheet table")
        assert result == mock_table
    
    def test_create_cell_with_text(self):
        """create_cell should create td element with text"""
        mock_cell = Mock()
        self.mock_xhtml_maker.td.return_value = mock_cell
        
        result = self.reporter.create_cell("test text")
        
        self.mock_xhtml_maker.td.assert_called_once_with("test text")
        assert result == mock_cell
    
    def test_create_cell_without_text(self):
        """create_cell should create empty td element when text is None"""
        mock_cell = Mock()
        self.mock_xhtml_maker.td.return_value = mock_cell
        
        result = self.reporter.create_cell(None)
        
        self.mock_xhtml_maker.td.assert_called_once_with()
        assert result == mock_cell
    
    def test_create_cell_default_parameter(self):
        """create_cell should create empty td element by default"""
        mock_cell = Mock()
        self.mock_xhtml_maker.td.return_value = mock_cell
        
        result = self.reporter.create_cell()
        
        self.mock_xhtml_maker.td.assert_called_once_with()
        assert result == mock_cell
    
    def test_add_row(self):
        """add_row should create tr element and append cells"""
        mock_table = Mock()
        mock_row = Mock()
        mock_cell1 = Mock()
        mock_cell2 = Mock()
        elements = [mock_cell1, mock_cell2]
        
        self.mock_xhtml_maker.tr.return_value = mock_row
        
        self.reporter.add_row(mock_table, elements)
        
        # Should create row with correct class
        self.mock_xhtml_maker.tr.assert_called_once_with({"class": "row"})
        
        # Should append all elements to row
        mock_row.append.assert_has_calls([call(mock_cell1), call(mock_cell2)])
        
        # Should append row to table
        mock_table.append.assert_called_once_with(mock_row)
    
    def test_add_empty_row(self):
        """add_empty_row should add row with single blank cell"""
        mock_table = Mock()
        mock_row = Mock()
        mock_blank_cell = Mock()
        
        self.mock_xhtml_maker.tr.return_value = mock_row
        self.mock_xhtml_maker.td.return_value = mock_blank_cell
        
        self.reporter.add_empty_row(mock_table)
        
        # Should create row
        self.mock_xhtml_maker.tr.assert_called_once_with({"class": "row"})
        
        # Should create blank cell with non-breaking space
        self.mock_xhtml_maker.td.assert_called_once_with("\u00a0")
        
        # Should set cell class
        mock_blank_cell.set.assert_called_once_with("class", "label cell")
        
        # Should append cell to row and row to table
        mock_row.append.assert_called_once_with(mock_blank_cell)
        mock_table.append.assert_called_once_with(mock_row)


class TestIxbrlReporterFormatting:
    """Test number formatting methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        
    def test_fmt_basic_formatting(self):
        """fmt should format numbers with decimals and scale"""
        self.reporter.decimals = 2
        self.reporter.scale = 0
        
        result = self.reporter.fmt(1234.567)
        
        # Should round to 2 decimals and format with thousands separator
        assert result == "1,234.57"
    
    def test_fmt_with_scale(self):
        """fmt should apply scale division"""
        self.reporter.decimals = 0
        self.reporter.scale = 3  # Divide by 1000
        
        result = self.reporter.fmt(1234567)
        
        # Should divide by 1000 and format as integer
        assert result == "1,235"
    
    def test_fmt_zero_decimals(self):
        """fmt should format as integer when decimals is 0"""
        self.reporter.decimals = 0
        self.reporter.scale = 0
        
        result = self.reporter.fmt(1234.789)
        
        # Should round to integer and format without decimals
        assert result == "1,235"
    
    def test_fmt_negative_numbers(self):
        """fmt should handle negative numbers correctly"""
        self.reporter.decimals = 2
        self.reporter.scale = 0
        
        result = self.reporter.fmt(-1234.567)
        
        # Should format negative numbers
        assert result == "-1,234.57"
    
    def test_fmt_high_decimals(self):
        """fmt should handle higher decimal places"""
        self.reporter.decimals = 4
        self.reporter.scale = 0
        
        result = self.reporter.fmt(123.456789)
        
        # Should format with 4 decimal places
        assert result == "123.4568"


class TestIxbrlReporterFactCreation:
    """Test fact creation methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        self.mock_par = Mock()
        self.mock_ix_maker = Mock()
        self.mock_xhtml_maker = Mock()
        self.mock_par.ix_maker = self.mock_ix_maker
        self.mock_par.xhtml_maker = self.mock_xhtml_maker
        self.reporter.par = self.mock_par
        
        # Set up formatting parameters
        self.reporter.decimals = 2
        self.reporter.scale = 0
        self.reporter.currency = "GBP"
        self.reporter.tiny = 0.005  # Half of 10^-decimals
    
    def test_create_tagged_money_fact_positive_value(self):
        """create_tagged_money_fact should create iXBRL element for positive values"""
        mock_fact = Mock()
        mock_fact.value = 1000.0
        mock_fact.name = "uk-gaap:TurnoverGrossOperatingRevenue"
        mock_fact.context = "context-1"
        mock_fact.reverse = False
        
        mock_ix_element = Mock()
        mock_spans = [Mock(), Mock(), Mock()]  # Multiple spans for positive case
        self.mock_ix_maker.nonFraction.return_value = mock_ix_element
        self.mock_xhtml_maker.span.side_effect = mock_spans
        
        result = self.reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Should create iXBRL nonFraction element with formatted text
        self.mock_ix_maker.nonFraction.assert_called_once_with("1,000.00")
        
        # Should set all required attributes
        mock_ix_element.set.assert_has_calls([
            call("name", "uk-gaap:TurnoverGrossOperatingRevenue"),
            call("contextRef", "context-1"),
            call("format", "ixt2:numdotdecimal"),
            call("unitRef", "GBP"),
            call("decimals", "2"),
            call("scale", "0")
        ], any_order=True)
        
        # Should not set sign attribute for positive values
        sign_calls = [c for c in mock_ix_element.set.call_args_list if c[0][0] == "sign"]
        assert len(sign_calls) == 0
        
        # Should create 3 spans for positive case
        assert self.mock_xhtml_maker.span.call_count == 3
        
        # Should append spans to main span
        mock_spans[0].append.assert_has_calls([
            call(mock_spans[1]),
            call(mock_ix_element),
            call(mock_spans[2])
        ])
        
        assert result == mock_spans[0]
    
    def test_create_tagged_money_fact_negative_value(self):
        """create_tagged_money_fact should handle negative values with parentheses"""
        mock_fact = Mock()
        mock_fact.value = -500.0
        mock_fact.name = "uk-gaap:AdministrativeExpenses"
        mock_fact.context = "context-1"
        mock_fact.reverse = False
        
        mock_ix_element = Mock()
        mock_spans = [Mock(), Mock(), Mock()]  # Main span + 2 inner spans
        
        self.mock_ix_maker.nonFraction.return_value = mock_ix_element
        self.mock_xhtml_maker.span.side_effect = mock_spans
        
        result = self.reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Should format absolute value
        self.mock_ix_maker.nonFraction.assert_called_once_with("500.00")
        
        # Should set sign attribute for negative values
        mock_ix_element.set.assert_any_call("sign", "-")
        
        # Should create 3 spans for negative case
        assert self.mock_xhtml_maker.span.call_count == 3
        
        # Should create parentheses structure
        mock_spans[0].append.assert_has_calls([
            call(mock_spans[1]),  # "( " span
            call(mock_ix_element), # The actual element  
            call(mock_spans[2])   # " )" span
        ])
        
        assert result == mock_spans[0]
    
    def test_create_tagged_money_fact_with_reverse_sign(self):
        """create_tagged_money_fact should handle reverse flag correctly"""
        mock_fact = Mock()
        mock_fact.value = 1000.0  # Positive value
        mock_fact.name = "uk-gaap:ProfitLoss"
        mock_fact.context = "context-1"
        mock_fact.reverse = True  # But reversed
        
        mock_ix_element = Mock()
        mock_spans = [Mock(), Mock(), Mock()]  # Multiple spans for positive display
        self.mock_ix_maker.nonFraction.return_value = mock_ix_element
        self.mock_xhtml_maker.span.side_effect = mock_spans
        
        result = self.reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Should set sign attribute even though value is positive (due to reverse=True)
        mock_ix_element.set.assert_any_call("sign", "-")
        
        # Should create spans for positive display (not parentheses) since actual value is positive
        assert self.mock_xhtml_maker.span.call_count == 3
        mock_spans[0].append.assert_has_calls([
            call(mock_spans[1]),
            call(mock_ix_element),
            call(mock_spans[2])
        ])
        
        assert result == mock_spans[0]
    
    def test_create_tagged_money_fact_tiny_value(self):
        """create_tagged_money_fact should treat tiny values as zero"""
        mock_fact = Mock()
        mock_fact.value = 0.001  # Smaller than tiny threshold (0.005)
        mock_fact.name = "uk-gaap:ProfitLoss"
        mock_fact.context = "context-1"
        mock_fact.reverse = False
        
        mock_ix_element = Mock()
        mock_span = Mock()
        self.mock_ix_maker.nonFraction.return_value = mock_ix_element
        self.mock_xhtml_maker.span.return_value = mock_span
        
        result = self.reporter.create_tagged_money_fact(mock_fact, "section")
        
        # Should format as usual but not set sign (treated as zero)
        self.mock_ix_maker.nonFraction.assert_called_once_with("0.00")
        
        # Should not set sign attribute for tiny values
        sign_calls = [c for c in mock_ix_element.set.call_args_list if c[0][0] == "sign"]
        assert len(sign_calls) == 0
        
        assert result == mock_span
    
    def test_create_untagged_money_fact(self):
        """create_untagged_money_fact should create plain text without iXBRL tags"""
        mock_fact = Mock()
        mock_fact.value = 1500.75
        
        # Set up formatting
        self.reporter.decimals = 2
        self.reporter.scale = 0
        
        mock_span = Mock()
        self.mock_xhtml_maker.span.return_value = mock_span
        
        result = self.reporter.create_untagged_money_fact(mock_fact, "section")
        
        # Should create span with formatted text
        self.mock_xhtml_maker.span.assert_called_once_with("1,500.75\u00a0\u00a0")
        assert result == mock_span
    
    def test_create_tagged_fact_non_money(self):
        """create_tagged_fact should handle non-money facts"""
        mock_fact = Mock()
        mock_fact.value = "Some text value"
        mock_fact.name = "uk-gaap:EntityCurrentLegalOrRegisteredName"
        mock_fact.context = "context-1"
        
        mock_ix_element = Mock()
        self.mock_ix_maker.nonFraction.return_value = mock_ix_element
        
        result = self.reporter.create_tagged_fact(mock_fact, "section")
        
        # Should create nonFraction iXBRL element (not nonNumeric)
        self.mock_ix_maker.nonFraction.assert_called_once_with("Some text value")
        
        # Should set name and context
        mock_ix_element.set.assert_has_calls([
            call("name", "uk-gaap:EntityCurrentLegalOrRegisteredName"),
            call("contextRef", "context-1")
        ], any_order=True)
        
        assert result == mock_ix_element
    
    def test_create_untagged_fact_non_money(self):
        """create_untagged_fact should return plain text for non-money facts"""
        mock_fact = Mock()
        mock_fact.value = "Plain text content"
        
        mock_span = Mock()
        self.mock_xhtml_maker.span.return_value = mock_span
        
        result = self.reporter.create_untagged_fact(mock_fact, "section")
        
        # Should create span with text value
        self.mock_xhtml_maker.span.assert_called_once_with("Plain text content")
        assert result == mock_span


class TestIxbrlReporterMaybeTag:
    """Test maybe_tag method for conditional tagging"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        self.mock_taxonomy = Mock()
        self.reporter.taxonomy = self.mock_taxonomy
    
    def test_maybe_tag_with_money_datum_tagged(self):
        """maybe_tag should create tagged money fact when taxonomy returns fact"""
        from ixbrl_reporter.datum import MoneyDatum
        
        mock_datum = Mock(spec=MoneyDatum)
        mock_fact = Mock()
        mock_fact.value = 1000.0
        self.mock_taxonomy.create_fact.return_value = mock_fact
        
        with patch.object(self.reporter, 'create_tagged_money_fact') as mock_create_tagged:
            mock_tagged_result = Mock()
            mock_create_tagged.return_value = mock_tagged_result
            
            result = self.reporter.maybe_tag(mock_datum, "section")
            
            # Should try to create fact from datum
            self.mock_taxonomy.create_fact.assert_called_once_with(mock_datum)
            
            # Should create tagged money fact
            mock_create_tagged.assert_called_once_with(mock_fact, "section")
            
            assert result == mock_tagged_result
    
    def test_maybe_tag_with_money_datum_untagged(self):
        """maybe_tag should create untagged money fact when taxonomy returns fact with no name"""
        from ixbrl_reporter.datum import MoneyDatum
        
        mock_datum = Mock(spec=MoneyDatum)
        mock_fact = Mock()
        mock_fact.name = None  # No name means untagged
        self.mock_taxonomy.create_fact.return_value = mock_fact
        
        with patch.object(self.reporter, 'create_untagged_money_fact') as mock_create_untagged:
            mock_untagged_result = Mock()
            mock_create_untagged.return_value = mock_untagged_result
            
            result = self.reporter.maybe_tag(mock_datum, "section")
            
            # Should try to create fact from datum
            self.mock_taxonomy.create_fact.assert_called_once_with(mock_datum)
            
            # Should create untagged money fact
            mock_create_untagged.assert_called_once_with(mock_fact, "section")
            
            assert result == mock_untagged_result
    
    def test_maybe_tag_with_non_money_datum_tagged(self):
        """maybe_tag should create tagged fact for non-money data when taxonomy returns fact"""
        mock_datum = Mock()  # Not MoneyDatum
        mock_fact = Mock()
        mock_fact.value = "text value"
        self.mock_taxonomy.create_fact.return_value = mock_fact
        
        with patch.object(self.reporter, 'create_tagged_fact') as mock_create_tagged:
            mock_tagged_result = Mock()
            mock_create_tagged.return_value = mock_tagged_result
            
            result = self.reporter.maybe_tag(mock_datum, "section")
            
            # Should create tagged fact
            mock_create_tagged.assert_called_once_with(mock_fact, "section")
            
            assert result == mock_tagged_result
    
    def test_maybe_tag_with_non_money_datum_untagged(self):
        """maybe_tag should create untagged fact for non-money data when taxonomy returns fact with no name"""
        mock_datum = Mock()  # Not MoneyDatum
        mock_fact = Mock()
        mock_fact.name = None  # No name means untagged
        self.mock_taxonomy.create_fact.return_value = mock_fact
        
        with patch.object(self.reporter, 'create_untagged_fact') as mock_create_untagged:
            mock_untagged_result = Mock()
            mock_create_untagged.return_value = mock_untagged_result
            
            result = self.reporter.maybe_tag(mock_datum, "section")
            
            # Should create untagged fact
            mock_create_untagged.assert_called_once_with(mock_fact, "section")
            
            assert result == mock_untagged_result


class TestIxbrlReporterHeaderGeneration:
    """Test header generation methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        self.mock_par = Mock()
        self.mock_xhtml_maker = Mock()
        self.mock_par.xhtml_maker = self.mock_xhtml_maker
        self.reporter.par = self.mock_par
    
    def test_add_column_headers(self):
        """add_column_headers should create header row with column titles"""
        mock_grid = Mock()
        # Create mock column tuples (col, span)
        mock_col1 = Mock()
        mock_col1.metadata.description = "Column 1"
        mock_col2 = Mock()
        mock_col2.metadata.description = "Column 2"
        mock_cols = [(mock_col1, 1), (mock_col2, 1)]
        
        # Mock create_cell to return appropriate cells
        # Need 4 cells: label cell + note cell (when notes not hidden) + 2 column cells
        mock_cells = [Mock(), Mock(), Mock(), Mock()]
        
        with patch.object(self.reporter, 'create_cell') as mock_create_cell:
            with patch.object(self.reporter, 'add_row') as mock_add_row:
                mock_create_cell.side_effect = mock_cells
                
                self.reporter.add_column_headers(mock_grid, mock_cols)
                
                # Should create cells with proper text
                assert mock_create_cell.call_count == 4
                mock_create_cell.assert_any_call("\u00a0")  # Empty label cell
                mock_create_cell.assert_any_call("\u00a0")  # Empty note cell
                mock_create_cell.assert_any_call("Column 1")
                mock_create_cell.assert_any_call("Column 2")
                
                # Should set classes and colspan on cells
                mock_cells[0].set.assert_called_with("class", "label cell")
                mock_cells[1].set.assert_called_with("class", "note")
                mock_cells[2].set.assert_any_call("class", "column header cell")
                mock_cells[2].set.assert_any_call("colspan", "1")
                mock_cells[3].set.assert_any_call("class", "column header cell")
                mock_cells[3].set.assert_any_call("colspan", "1")
                
                # Should add row to grid
                mock_add_row.assert_called_once()
    
    def test_add_currency_subheaders(self):
        """add_currency_subheaders should create currency subheader row"""
        mock_grid = Mock()
        # Create mock column tuples with units
        mock_col1 = Mock()
        mock_col1.units = "USD"
        mock_col2 = Mock()
        mock_col2.units = "USD"
        mock_cols = [(mock_col1, 1), (mock_col2, 1)]
        
        # Mock create_cell to return appropriate cells
        # Need 4 cells: label cell + note cell (when notes not hidden) + 2 currency cells
        mock_cells = [Mock(), Mock(), Mock(), Mock()]
        
        with patch.object(self.reporter, 'create_cell') as mock_create_cell:
            with patch.object(self.reporter, 'add_row') as mock_add_row:
                mock_create_cell.side_effect = mock_cells
                
                self.reporter.add_currency_subheaders(mock_grid, mock_cols)
                
                # Should create currency headers
                assert mock_create_cell.call_count == 4
                mock_create_cell.assert_any_call("\u00a0")  # Empty label cell
                mock_create_cell.assert_any_call("note")  # Note header cell
                mock_create_cell.assert_any_call("USD")
                mock_create_cell.assert_any_call("USD")
                
                # Should set classes and colspan on cells
                mock_cells[0].set.assert_called_with("class", "label cell")
                mock_cells[1].set.assert_called_with("class", "note header")
                mock_cells[2].set.assert_any_call("class", "column currency cell")
                mock_cells[2].set.assert_any_call("colspan", "1")
                mock_cells[3].set.assert_any_call("class", "column currency cell")
                mock_cells[3].set.assert_any_call("colspan", "1")
                
                # Should add row to grid
                mock_add_row.assert_called_once()


class TestIxbrlReporterRowGeneration:
    """Test row generation methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        self.mock_par = Mock()
        self.mock_xhtml_maker = Mock()
        self.mock_par.xhtml_maker = self.mock_xhtml_maker
        self.reporter.par = self.mock_par
        self.reporter.taxonomy = Mock()  # Add taxonomy mock
        
        # Mock table structure
        self.mock_table = Mock()
        self.mock_table.get_cols.return_value = [Mock(), Mock()]
    
    def test_add_row_ix_with_data(self):
        """add_row_ix should create data row with cells"""
        from ixbrl_reporter.table import Row, TotalIndex
        
        # Mock a regular row (not TotalIndex)
        mock_row_obj = Mock()
        mock_row_obj.metadata.description = "Test Row"
        mock_row_obj.notes = None
        
        # Mock child with values
        mock_child = Mock()
        mock_values = [Mock(), Mock()]
        mock_values[0].value = Mock()
        mock_values[0].value.context = "ctx1"
        mock_values[1].value = Mock()
        mock_values[1].value.context = "ctx2"
        mock_child.values = mock_values
        mock_row_obj.child = mock_child
        
        # Mock create_cell and description fact
        mock_desc_fact = Mock()
        mock_desc_fact.to_elt.return_value = Mock()
        self.reporter.taxonomy.create_description_fact.return_value = mock_desc_fact
        
        with patch.object(self.reporter, 'create_cell') as mock_create_cell:
            with patch.object(self.reporter, 'maybe_tag') as mock_maybe_tag:
                with patch.object(self.reporter, 'add_note') as mock_add_note:
                    with patch.object(self.reporter, 'add_row') as mock_add_row:
                        # Mock cells
                        mock_label_cell = Mock()
                        mock_data_cells = [Mock(), Mock()]
                        mock_create_cell.side_effect = [mock_label_cell] + mock_data_cells
                        mock_maybe_tag.side_effect = ["Tagged Data 1", "Tagged Data 2"]
                        
                        self.reporter.add_row_ix(self.mock_table, mock_row_obj)
                        
                        # Should create description fact
                        self.reporter.taxonomy.create_description_fact.assert_called_once_with(
                            mock_row_obj.metadata, mock_row_obj.metadata.description, "ctx1"
                        )
                        
                        # Should create label cell with description
                        mock_label_cell.set.assert_called_with("class", "label breakdown item cell")
                        mock_label_cell.append.assert_called_once()
                        
                        # Should create data cells and tag them
                        assert mock_maybe_tag.call_count == 2
                        mock_maybe_tag.assert_any_call(mock_values[0].value, mock_values[0].value)
                        mock_maybe_tag.assert_any_call(mock_values[1].value, mock_values[1].value)
                        
                        # Should append tagged content to cells
                        mock_data_cells[0].append.assert_called_once_with("Tagged Data 1")
                        mock_data_cells[1].append.assert_called_once_with("Tagged Data 2")
                        
                        # Should add note and row
                        mock_add_note.assert_called_once()
                        mock_add_row.assert_called_once()
    
    def test_add_single_line_ix_with_totals(self):
        """add_single_line_ix should create single line with totals"""
        from ixbrl_reporter.table import TotalIndex
        
        mock_row_obj = Mock()
        mock_row_obj.metadata.description = "Total Row"
        mock_row_obj.metadata = Mock()  # Ensure metadata exists
        mock_row_obj.notes = None
        
        # Mock child with values
        mock_child = Mock()
        mock_values = [Mock()]
        mock_values[0].value = Mock()
        mock_values[0].value.context = "ctx1"
        mock_child.values = mock_values
        mock_row_obj.child = mock_child
        
        # Mock description fact
        mock_desc_fact = Mock()
        mock_desc_fact.to_elt.return_value = Mock()
        self.reporter.taxonomy.create_description_fact.return_value = mock_desc_fact
        
        with patch.object(self.reporter, 'create_cell') as mock_create_cell:
            with patch.object(self.reporter, 'maybe_tag') as mock_maybe_tag:
                with patch.object(self.reporter, 'add_note') as mock_add_note:
                    with patch.object(self.reporter, 'add_row') as mock_add_row:
                        mock_label_cell = Mock()
                        mock_data_cell = Mock()
                        mock_create_cell.side_effect = [mock_label_cell, mock_data_cell]
                        mock_maybe_tag.return_value = "Tagged Total"
                        
                        self.reporter.add_single_line_ix(self.mock_table, mock_row_obj)
                        
                        # Should create description fact
                        self.reporter.taxonomy.create_description_fact.assert_called_once_with(
                            mock_row_obj.metadata, mock_row_obj.metadata.description, "ctx1"
                        )
                        
                        # Should create label cell
                        mock_label_cell.set.assert_called_with("class", "label heading total cell")
                        mock_label_cell.append.assert_called_once()
                        
                        # Should create and tag single data cell
                        mock_maybe_tag.assert_called_once_with(mock_values[0].value, mock_values[0].value)
                        mock_data_cell.append.assert_called_once_with("Tagged Total")
                        
                        # Should add note and row
                        mock_add_note.assert_called_once()
                        mock_add_row.assert_called_once()
    
    def test_add_note_with_notes_enabled(self):
        """add_note should add note cell when notes are not hidden"""
        self.reporter.hide_notes = False
        
        mock_row_obj = Mock()
        mock_row_obj.notes = "This is a note"
        
        mock_row = []
        mock_note_cell = Mock()
        self.mock_xhtml_maker.td.return_value = mock_note_cell
        
        self.reporter.add_note(mock_row_obj, mock_row)
        
        # Should create note cell
        self.mock_xhtml_maker.td.assert_called_once_with("This is a note")
        mock_note_cell.set.assert_called_once_with("class", "note")
        
        # Should append to row
        assert mock_note_cell in mock_row
    
    def test_add_note_with_notes_disabled(self):
        """add_note should not add note cell when notes are hidden"""
        self.reporter.hide_notes = True
        
        mock_row_obj = Mock()
        mock_row_obj.get_note.return_value = "This is a note"
        
        mock_row = []
        
        self.reporter.add_note(mock_row_obj, mock_row)
        
        # Should not create any cells
        self.mock_xhtml_maker.td.assert_not_called()
        
        # Row should remain empty
        assert len(mock_row) == 0
    
    def test_add_note_with_no_note(self):
        """add_note should handle rows without notes gracefully"""
        self.reporter.hide_notes = False
        
        mock_row_obj = Mock()
        mock_row_obj.notes = None
        
        mock_row = []
        mock_empty_cell = Mock()
        self.mock_xhtml_maker.td.return_value = mock_empty_cell
        
        self.reporter.add_note(mock_row_obj, mock_row)
        
        # Should create empty cell for None note
        self.mock_xhtml_maker.td.assert_called_once_with()
        mock_empty_cell.set.assert_called_once_with("class", "note")
        assert mock_empty_cell in mock_row
    
    def test_add_heading_ix(self):
        """add_heading_ix should create heading row"""
        mock_row_obj = Mock()
        mock_row_obj.metadata.description = "Section Heading"
        mock_row_obj.metadata = Mock()  # Ensure metadata exists
        mock_row_obj.notes = None
        
        # Mock child structure for heading
        mock_child = [Mock()]
        mock_child[0].child = Mock()
        mock_child[0].child.values = [Mock()]
        mock_child[0].child.values[0].value = Mock()
        mock_child[0].child.values[0].value.context = "ctx1"
        mock_row_obj.child = mock_child
        
        # Mock description fact
        mock_desc_fact = Mock()
        mock_desc_fact.to_elt.return_value = Mock()
        self.reporter.taxonomy.create_description_fact.return_value = mock_desc_fact
        
        with patch.object(self.reporter, 'create_cell') as mock_create_cell:
            with patch.object(self.reporter, 'add_note') as mock_add_note:
                with patch.object(self.reporter, 'add_row') as mock_add_row:
                    mock_heading_cell = Mock()
                    mock_create_cell.return_value = mock_heading_cell
                    
                    self.reporter.add_heading_ix(self.mock_table, mock_row_obj)
                    
                    # Should create description fact
                    self.reporter.taxonomy.create_description_fact.assert_called_once_with(
                        mock_row_obj.metadata, mock_row_obj.metadata.description, "ctx1"
                    )
                    
                    # Should create heading cell with appropriate class
                    mock_heading_cell.set.assert_called_with("class", "label breakdown heading cell")
                    mock_heading_cell.append.assert_called_once()
                    
                    # Should add note and row
                    mock_add_note.assert_called_once()
                    mock_add_row.assert_called_once()


class TestIxbrlReporterReportGeneration:
    """Test main report generation methods"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
        self.mock_par = Mock()
        self.mock_taxonomy = Mock()
        self.mock_data = Mock()
        
        # Set up configuration values
        self.mock_data.get_config.side_effect = lambda key, default=None: {
            "metadata.accounting.decimals": 2,
            "metadata.accounting.scale": 0,
            "metadata.accounting.currency": "GBP"
        }.get(key, default)
    
    def test_get_elt_initialization(self):
        """get_elt should initialize reporter with parameters and configuration"""
        mock_worksheet = Mock()
        
        with patch.object(self.reporter, 'create_report') as mock_create_report:
            mock_result = Mock()
            mock_create_report.return_value = mock_result
            
            result = self.reporter.get_elt(
                mock_worksheet, self.mock_par, self.mock_taxonomy, self.mock_data
            )
            
            # Should set instance variables
            assert self.reporter.par == self.mock_par
            assert self.reporter.taxonomy == self.mock_taxonomy
            assert self.reporter.data == self.mock_data
            
            # Should load configuration
            assert self.reporter.decimals == 2
            assert self.reporter.scale == 0
            assert self.reporter.currency == "GBP"
            assert self.reporter.tiny == 0.005  # (10^-2) / 2
            
            # Should create report
            mock_create_report.assert_called_once_with(mock_worksheet)
            
            assert result == mock_result
    
    def test_create_report_basic_structure(self):
        """create_report should create basic table structure"""
        mock_worksheet = Mock()
        mock_ds = Mock()
        mock_ds.has_notes.return_value = True
        mock_worksheet.get_table.return_value = mock_ds
        
        # Set up reporter with required attributes
        self.reporter.taxonomy = Mock()
        
        with patch.object(self.reporter, 'create_table') as mock_create_table:
            with patch.object(self.reporter, 'add_header') as mock_add_header:
                with patch.object(self.reporter, 'add_body') as mock_add_body:
                    mock_grid = Mock()
                    mock_create_table.return_value = mock_grid
                    
                    result = self.reporter.create_report(mock_worksheet)
                    
                    # Should create table
                    mock_create_table.assert_called_once()
                    
                    # Should add header and body
                    mock_add_header.assert_called_once_with(mock_ds, mock_grid)
                    mock_add_body.assert_called_once_with(mock_ds, mock_grid)
                    
                    assert result == mock_grid


class TestIxbrlReporterIntegration:
    """Integration tests for IxbrlReporter"""
    
    def setup_method(self):
        """Set up integration test fixtures"""
        self.reporter = IxbrlReporter(hide_notes=False)
    
    def test_formatting_integration(self):
        """Test integration between formatting methods"""
        # Test realistic formatting scenarios
        self.reporter.decimals = 2
        self.reporter.scale = 3  # Thousands
        
        # Test large number with scale
        result = self.reporter.fmt(1234567.89)
        assert result == "1,234.57"
        
        # Test formatting consistency
        self.reporter.decimals = 0
        self.reporter.scale = 0
        
        result = self.reporter.fmt(999.99)
        assert result == "1,000"
    
    def test_tiny_threshold_calculation(self):
        """Test tiny threshold calculation with different decimal settings"""
        mock_data = Mock()
        mock_data.get_config.side_effect = lambda key, default=None: {
            "metadata.accounting.decimals": 3,  # 3 decimal places
            "metadata.accounting.scale": 0,
            "metadata.accounting.currency": "EUR"
        }.get(key, default)
        
        # Mock worksheet and its table
        mock_worksheet = Mock()
        mock_ds = Mock()
        mock_ds.has_notes.return_value = True
        mock_ds.header_levels.return_value = 0  # No header levels to avoid loop
        mock_ds.ixs = []  # No body items to process
        mock_worksheet.get_table.return_value = mock_ds
        
        # Initialize with 3 decimals
        result = self.reporter.get_elt(mock_worksheet, Mock(), Mock(), mock_data)
        
        # Tiny should be (10^-3) / 2 = 0.0005
        assert self.reporter.tiny == 0.0005
    
    def test_end_to_end_fact_creation_workflow(self):
        """Test complete workflow from datum to fact creation"""
        from ixbrl_reporter.datum import MoneyDatum
        
        # Set up full reporter
        self.reporter.par = Mock()
        self.reporter.par.ix_maker = Mock()
        self.reporter.par.xhtml_maker = Mock()
        self.reporter.taxonomy = Mock()
        self.reporter.decimals = 2
        self.reporter.scale = 0
        self.reporter.currency = "USD"
        self.reporter.tiny = 0.005
        
        # Create realistic datum
        mock_datum = Mock(spec=MoneyDatum)
        mock_fact = Mock()
        mock_fact.value = 1500.75
        mock_fact.name = "us-gaap:Revenues"
        mock_fact.context = "duration-context"
        mock_fact.reverse = False
        
        # Set up taxonomy to return fact
        self.reporter.taxonomy.create_fact.return_value = mock_fact
        
        # Set up element creation
        mock_ix_element = Mock()
        mock_span = Mock()
        self.reporter.par.ix_maker.nonFraction.return_value = mock_ix_element
        self.reporter.par.xhtml_maker.span.return_value = mock_span
        
        # Execute workflow
        result = self.reporter.maybe_tag(mock_datum, "revenues")
        
        # Verify complete workflow
        self.reporter.taxonomy.create_fact.assert_called_once_with(mock_datum)
        self.reporter.par.ix_maker.nonFraction.assert_called_once_with("1,500.75")
        
        # Verify iXBRL attributes
        mock_ix_element.set.assert_any_call("name", "us-gaap:Revenues")
        mock_ix_element.set.assert_any_call("contextRef", "duration-context")
        mock_ix_element.set.assert_any_call("unitRef", "USD")
        
        assert result == mock_span