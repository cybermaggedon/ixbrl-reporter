"""
Unit tests for ixbrl_reporter.debug_reporter module
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from io import StringIO

from ixbrl_reporter.debug_reporter import DebugReporter


class TestDebugReporterInit:
    """Test DebugReporter initialization"""
    
    def test_debug_reporter_creation(self):
        """DebugReporter should initialize without parameters"""
        reporter = DebugReporter()
        assert isinstance(reporter, DebugReporter)
        assert hasattr(reporter, 'output')
        assert hasattr(reporter, 'handle')


class TestDebugReporterOutput:
    """Test DebugReporter.output method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.mock_ws = Mock()
        self.mock_taxonomy = Mock()
        self.output = StringIO()
    
    def test_output_calls_worksheet_get_table(self):
        """output should call worksheet.get_table with taxonomy"""
        mock_table = Mock()
        self.mock_ws.get_table.return_value = mock_table
        
        with patch.object(self.reporter, 'handle') as mock_handle:
            self.reporter.output(self.mock_ws, self.output, self.mock_taxonomy)
        
        # Verify get_table was called with taxonomy
        self.mock_ws.get_table.assert_called_once_with(self.mock_taxonomy)
        
        # Verify handle was called with table and output
        mock_handle.assert_called_once_with(mock_table, self.output)
    
    def test_output_passes_table_to_handle(self):
        """output should pass table from worksheet to handle method"""
        mock_table = Mock()
        self.mock_ws.get_table.return_value = mock_table
        
        with patch.object(self.reporter, 'handle') as mock_handle:
            self.reporter.output(self.mock_ws, self.output, self.mock_taxonomy)
        
        # Verify handle received the correct table
        mock_handle.assert_called_once_with(mock_table, self.output)
    
    def test_output_with_different_worksheets(self):
        """output should work with different worksheet objects"""
        worksheets = [Mock(), Mock(), Mock()]
        tables = [Mock(), Mock(), Mock()]
        
        for ws, table in zip(worksheets, tables):
            ws.get_table.return_value = table
            
            with patch.object(self.reporter, 'handle') as mock_handle:
                self.reporter.output(ws, self.output, self.mock_taxonomy)
                
                ws.get_table.assert_called_once_with(self.mock_taxonomy)
                mock_handle.assert_called_once_with(table, self.output)


class TestDebugReporterHandleTable:
    """Test DebugReporter.handle method with Table objects"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_handle_table_basic_structure(self):
        """handle should process Table objects correctly"""
        # Create mock Table
        mock_table = Mock()
        mock_table.__class__.__name__ = 'Table'
        
        # Configure Table properties
        mock_table.columns = []
        mock_table.ixs = []
        mock_table.header_levels.return_value = 2
        mock_table.column_count.return_value = 5
        mock_table.row_count.return_value = 10
        mock_table.ix_levels.return_value = 3
        
        # Need to mock isinstance checks
        with patch('ixbrl_reporter.debug_reporter.isinstance') as mock_isinstance:
            def isinstance_side_effect(obj, class_type):
                if obj == mock_table and class_type.__name__ == 'Table':
                    return True
                return False
            
            mock_isinstance.side_effect = isinstance_side_effect
            
            with patch('builtins.print') as mock_print:
                self.reporter.handle(mock_table, self.output)
            
            # Verify Table methods were called
            mock_table.header_levels.assert_called_once()
            mock_table.column_count.assert_called_once()
            mock_table.row_count.assert_called_once()
            mock_table.ix_levels.assert_called_once()
            
            # Verify print statements
            expected_calls = [
                call("Table:"),
                call(),
                call("Table has", 2, "header levels"),
                call("Table has", 5, "columns"),
                call("Table has", 10, "rows"),
                call("Table has", 3, "index levels")
            ]
            mock_print.assert_has_calls(expected_calls)
    
    def test_handle_table_with_columns(self):
        """handle should recursively process Table columns"""
        # Import real classes for isinstance checks
        from ixbrl_reporter.table import Table, Column
        
        mock_table = Mock(spec=Table)
        mock_col1 = Mock(spec=Column)
        mock_col2 = Mock(spec=Column) 
        
        # Set up metadata for columns
        mock_col1.metadata = Mock(description="Column 1")
        mock_col2.metadata = Mock(description="Column 2")
        mock_col1.children = None
        mock_col2.children = None
        
        mock_table.columns = [mock_col1, mock_col2]
        mock_table.ixs = []
        mock_table.header_levels.return_value = 1
        mock_table.column_count.return_value = 2
        mock_table.row_count.return_value = 5
        mock_table.ix_levels.return_value = 1
        
        with patch('builtins.print'):
            with patch.object(self.reporter, 'handle', wraps=self.reporter.handle) as mock_handle:
                self.reporter.handle(mock_table, self.output)
        
        # Should have called handle recursively for each column
        expected_calls = [
            call(mock_table, self.output),  # Original call
            call(mock_col1, self.output, 1),  # Column 1 with indent
            call(mock_col2, self.output, 1)   # Column 2 with indent
        ]
        mock_handle.assert_has_calls(expected_calls)
    
    def test_handle_table_with_indexes(self):
        """handle should recursively process Table indexes"""
        from ixbrl_reporter.table import Table, Index, Row
        
        mock_table = Mock(spec=Table)
        mock_ix1 = Mock(spec=Index)
        mock_ix2 = Mock(spec=Index)
        
        # Set up metadata for indexes
        mock_ix1.metadata = Mock(description="Index 1")
        mock_ix2.metadata = Mock(description="Index 2")
        # Simple rows with empty values
        mock_ix1.child = Mock(spec=Row, values=[])
        mock_ix2.child = Mock(spec=Row, values=[])
        
        mock_table.columns = []
        mock_table.ixs = [mock_ix1, mock_ix2]
        mock_table.header_levels.return_value = 1
        mock_table.column_count.return_value = 2
        mock_table.row_count.return_value = 5
        mock_table.ix_levels.return_value = 2
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_table, self.output)
        
        # Should have printed table info and index descriptions
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Table:" in call for call in print_calls)
        assert any("Index 1" in call for call in print_calls)
        assert any("Index 2" in call for call in print_calls)


class TestDebugReporterHandleColumn:
    """Test DebugReporter.handle method with Column objects"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_handle_column_basic(self):
        """handle should process Column objects correctly"""
        from ixbrl_reporter.table import Column
        
        mock_column = Mock(spec=Column)
        mock_metadata = Mock()
        mock_metadata.description = "Test Column"
        mock_column.metadata = mock_metadata
        mock_column.children = None
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_column, self.output, indent=2)
        
        # Verify output was written with correct indentation
        output_content = self.output.getvalue()
        assert "    " in output_content  # 2 * 2 spaces for indent=2
        
        # Verify print was called with column description
        mock_print.assert_called_once_with("Column:", "Test Column")
    
    def test_handle_column_with_children(self):
        """handle should recursively process Column children"""
        from ixbrl_reporter.table import Column
        
        mock_column = Mock(spec=Column)
        mock_metadata = Mock()
        mock_metadata.description = "Parent Column"
        mock_column.metadata = mock_metadata
        
        mock_child1 = Mock(spec=Column)
        mock_child2 = Mock(spec=Column)
        # Set up child metadata
        mock_child1.metadata = Mock(description="Child 1")
        mock_child2.metadata = Mock(description="Child 2")
        mock_child1.children = None
        mock_child2.children = None
        mock_column.children = [mock_child1, mock_child2]
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_column, self.output, indent=1)
        
        # Should have printed parent and children
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Parent Column" in call for call in print_calls)
        assert any("Child 1" in call for call in print_calls)
        assert any("Child 2" in call for call in print_calls)
    
    def test_handle_column_without_children(self):
        """handle should handle Column without children"""
        from ixbrl_reporter.table import Column
        
        mock_column = Mock(spec=Column)
        mock_metadata = Mock()
        mock_metadata.description = "Leaf Column"
        mock_column.metadata = mock_metadata
        mock_column.children = None
        
        with patch('builtins.print') as mock_print:
            with patch.object(self.reporter, 'handle', wraps=self.reporter.handle) as mock_handle:
                self.reporter.handle(mock_column, self.output)
        
        # Should only call handle once (no children to recurse)
        mock_handle.assert_called_once_with(mock_column, self.output)
        mock_print.assert_called_once_with("Column:", "Leaf Column")


class TestDebugReporterHandleIndex:
    """Test DebugReporter.handle method with Index objects"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_handle_regular_index(self):
        """handle should process regular Index objects"""
        from ixbrl_reporter.table import Index, Row
        
        mock_index = Mock(spec=Index)
        mock_metadata = Mock()
        mock_metadata.description = "Test Index"
        mock_index.metadata = mock_metadata
        mock_row = Mock(spec=Row)
        mock_row.values = []
        mock_index.child = mock_row
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_index, self.output, indent=1)
        
        # Should print both index description and row
        print_calls = [call[0] for call in mock_print.call_args_list]
        assert ("Index:", "Test Index") in print_calls
        assert ("Row:",) in print_calls
    
    def test_handle_total_index(self):
        """handle should process TotalIndex objects differently"""
        from ixbrl_reporter.table import TotalIndex, Row
        
        mock_total_index = Mock(spec=TotalIndex)
        mock_metadata = Mock()
        mock_metadata.description = "Total Index"
        mock_total_index.metadata = mock_metadata
        mock_row = Mock(spec=Row)
        mock_row.values = []
        mock_total_index.child = mock_row
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_total_index, self.output)
        
        # Should print both Total and Row
        print_calls = [call[0] for call in mock_print.call_args_list]
        assert ("Total:",) in print_calls
        assert ("Row:",) in print_calls
    
    def test_handle_index_with_index_children(self):
        """handle should process Index with Index children (not Row)"""
        from ixbrl_reporter.table import Index, Row
        
        mock_index = Mock(spec=Index)
        mock_metadata = Mock()
        mock_metadata.description = "Parent Index"
        mock_index.metadata = mock_metadata
        
        mock_child1 = Mock(spec=Index)
        mock_child2 = Mock(spec=Index)
        # Set up child metadata
        mock_child1.metadata = Mock(description="Child Index 1")
        mock_child2.metadata = Mock(description="Child Index 2")
        mock_child1.child = Mock(spec=Row, values=[])
        mock_child2.child = Mock(spec=Row, values=[])
        
        mock_index.child = [mock_child1, mock_child2]  # List of indexes, not Row
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_index, self.output, indent=2)
        
        # Should print parent and child indexes
        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Parent Index" in call for call in print_calls)
        assert any("Child Index 1" in call for call in print_calls)
        assert any("Child Index 2" in call for call in print_calls)


class TestDebugReporterHandleRow:
    """Test DebugReporter.handle method with Row objects"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_handle_row_basic(self):
        """handle should process Row objects correctly"""
        from ixbrl_reporter.table import Row, Cell
        
        mock_row = Mock(spec=Row)
        mock_cell1 = Mock(spec=Cell)
        mock_cell1.value = Mock(value="test1")
        mock_cell2 = Mock(spec=Cell)
        mock_cell2.value = Mock(value="test2")
        mock_row.values = [mock_cell1, mock_cell2]
        
        with patch('builtins.print') as mock_print:
            with patch.object(self.reporter, 'handle', wraps=self.reporter.handle) as mock_handle:
                self.reporter.handle(mock_row, self.output, indent=3)
        
        # Verify print was called (should be 3 times: Row + 2 cells)
        print_calls = [call[0] for call in mock_print.call_args_list]
        assert ("Row:",) in print_calls
        assert ("Cell:", "test1") in print_calls
        assert ("Cell:", "test2") in print_calls
        
        # Verify indentation was written
        output_content = self.output.getvalue()
        assert "      " in output_content  # 3 * 2 spaces
        
        # Should recursively handle each cell
        expected_calls = [
            call(mock_row, self.output, indent=3),
            call(mock_cell1, self.output, 4),
            call(mock_cell2, self.output, 4)  
        ]
        mock_handle.assert_has_calls(expected_calls)
    
    def test_handle_row_empty_values(self):
        """handle should handle Row with empty values"""
        from ixbrl_reporter.table import Row
        
        mock_row = Mock(spec=Row)
        mock_row.values = []
        
        with patch('builtins.print') as mock_print:
            with patch.object(self.reporter, 'handle', wraps=self.reporter.handle) as mock_handle:
                self.reporter.handle(mock_row, self.output)
        
        # Should still print "Row:" but not recurse
        mock_print.assert_called_once_with("Row:")
        mock_handle.assert_called_once_with(mock_row, self.output)


class TestDebugReporterHandleCell:
    """Test DebugReporter.handle method with Cell objects"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_handle_cell_with_float_value(self):
        """handle should format float Cell values with rounding"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = 123.456789
        mock_cell.value = mock_value
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_cell, self.output, indent=1)
        
        # Should print rounded float value
        mock_print.assert_called_once_with("Cell:", 123.46)
        
        # Verify indentation
        output_content = self.output.getvalue()
        assert "  " in output_content  # 1 * 2 spaces
    
    def test_handle_cell_with_string_value(self):
        """handle should display string Cell values as-is"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = "Test String Value"
        mock_cell.value = mock_value
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_cell, self.output)
        
        # Should print string value without modification
        mock_print.assert_called_once_with("Cell:", "Test String Value")
    
    def test_handle_cell_with_integer_value(self):
        """handle should display integer Cell values as-is"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = 42
        mock_cell.value = mock_value
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_cell, self.output, indent=2)
        
        # Should print integer value without rounding
        mock_print.assert_called_once_with("Cell:", 42)
    
    def test_handle_cell_with_none_value(self):
        """handle should handle Cell with None value"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = None
        mock_cell.value = mock_value
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_cell, self.output)
        
        # Should print None value
        mock_print.assert_called_once_with("Cell:", None)
    
    def test_handle_cell_with_boolean_value(self):
        """handle should handle Cell with boolean value"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = True
        mock_cell.value = mock_value
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_cell, self.output)
        
        # Should print boolean value
        mock_print.assert_called_once_with("Cell:", True)


class TestDebugReporterHandleIndentation:
    """Test indentation handling in DebugReporter.handle method"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_default_indent_is_zero(self):
        """handle should use indent=0 by default"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = "test"
        mock_cell.value = mock_value
        
        with patch('builtins.print'):
            self.reporter.handle(mock_cell, self.output)
        
        # Should have no indentation (empty string)
        output_content = self.output.getvalue()
        assert output_content == ""  # No spaces written for indent=0
    
    def test_indent_calculation(self):
        """handle should calculate indentation correctly (2 spaces per level)"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = "test"
        mock_cell.value = mock_value
        
        test_cases = [
            (0, ""),      # 0 * 2 = 0 spaces
            (1, "  "),    # 1 * 2 = 2 spaces
            (2, "    "),  # 2 * 2 = 4 spaces
            (3, "      "), # 3 * 2 = 6 spaces
            (5, "          ")  # 5 * 2 = 10 spaces
        ]
        
        for indent_level, expected_spaces in test_cases:
            output = StringIO()
            
            with patch('builtins.print'):
                self.reporter.handle(mock_cell, output, indent=indent_level)
            
            output_content = output.getvalue()
            assert output_content == expected_spaces


class TestDebugReporterIntegration:
    """Integration tests for DebugReporter"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_complete_workflow(self):
        """Test complete workflow from output to handle"""
        from ixbrl_reporter.table import Table, Column, Row, Cell
        
        # Create a realistic table structure
        mock_ws = Mock()
        mock_taxonomy = Mock()
        
        # Create table with basic structure
        mock_table = Mock(spec=Table)
        mock_column = Mock(spec=Column)
        mock_row = Mock(spec=Row)
        mock_cell = Mock(spec=Cell)
        
        # Set up table structure
        mock_table.columns = [mock_column]
        mock_table.ixs = []
        mock_table.header_levels.return_value = 1
        mock_table.column_count.return_value = 1
        mock_table.row_count.return_value = 1
        mock_table.ix_levels.return_value = 1
        
        # Set up column
        mock_metadata = Mock()
        mock_metadata.description = "Test Column"
        mock_column.metadata = mock_metadata
        mock_column.children = None
        
        mock_ws.get_table.return_value = mock_table
        
        with patch('builtins.print') as mock_print:
            self.reporter.output(mock_ws, self.output, mock_taxonomy)
        
        # Should have called worksheet.get_table
        mock_ws.get_table.assert_called_once_with(mock_taxonomy)
        
        # Should have printed table information
        print_calls = [call[0] for call in mock_print.call_args_list]
        assert ("Table:",) in print_calls
        assert ("Column:", "Test Column") in print_calls
    
    def test_deep_recursion_structure(self):
        """Test handling of deeply nested table structures"""
        from ixbrl_reporter.table import Table, Column, Index, Row, Cell, TotalIndex
        
        # Create deeply nested structure
        mock_table = Mock(spec=Table)
        mock_column = Mock(spec=Column)
        mock_child_column = Mock(spec=Column)
        mock_index = Mock(spec=Index)
        mock_total_index = Mock(spec=TotalIndex)
        mock_row = Mock(spec=Row)
        mock_cell = Mock(spec=Cell)
        
        # Setup nested structure
        mock_table.columns = [mock_column]
        mock_table.ixs = [mock_index, mock_total_index]
        mock_table.header_levels.return_value = 2
        mock_table.column_count.return_value = 2
        mock_table.row_count.return_value = 3
        mock_table.ix_levels.return_value = 2
        
        # Column with child
        mock_metadata = Mock()
        mock_metadata.description = "Parent Column"
        mock_column.metadata = mock_metadata
        mock_column.children = [mock_child_column]
        
        mock_child_metadata = Mock()
        mock_child_metadata.description = "Child Column"
        mock_child_column.metadata = mock_child_metadata
        mock_child_column.children = None
        
        # Index with Row
        mock_index_metadata = Mock()
        mock_index_metadata.description = "Test Index"
        mock_index.metadata = mock_index_metadata
        mock_index.child = mock_row
        
        # TotalIndex
        mock_total_metadata = Mock()
        mock_total_metadata.description = "Total"
        mock_total_index.metadata = mock_total_metadata
        mock_total_index.child = mock_row
        
        # Row with Cell
        mock_value = Mock()
        mock_value.value = 42.123
        mock_cell.value = mock_value
        mock_row.values = [mock_cell]
        
        with patch('builtins.print') as mock_print:
            self.reporter.handle(mock_table, self.output)
        
        # Verify all components were processed
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Check that all expected components appear in output
        assert any("Table:" in call for call in print_calls)
        assert any("Parent Column" in call for call in print_calls)
        assert any("Child Column" in call for call in print_calls)
        assert any("Test Index" in call for call in print_calls)
        assert any("Total:" in call for call in print_calls)
        assert any("Row:" in call for call in print_calls)
        assert any("42.12" in call for call in print_calls)  # Rounded float


class TestDebugReporterErrorCases:
    """Test error cases and edge conditions"""
    
    def setup_method(self):
        """Set up common test fixtures"""
        self.reporter = DebugReporter()
        self.output = StringIO()
    
    def test_handle_unknown_object_type(self):
        """handle should gracefully handle unknown object types"""
        unknown_object = Mock()
        unknown_object.__class__.__name__ = 'UnknownType'
        
        # Should not crash - just does nothing for unknown types
        with patch('builtins.print') as mock_print:
            self.reporter.handle(unknown_object, self.output)
        
        # Should not print anything for unknown types
        mock_print.assert_not_called()
        
        # Should not write any indentation
        output_content = self.output.getvalue()
        assert output_content == ""
    
    def test_handle_cell_with_attribute_error(self):
        """handle should handle Cell objects with missing attributes"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        # Don't set up mock_cell.value to simulate AttributeError
        del mock_cell.value
        
        with pytest.raises(AttributeError):
            self.reporter.handle(mock_cell, self.output)
    
    def test_output_with_worksheet_error(self):
        """output should handle worksheet.get_table errors"""
        mock_ws = Mock()
        mock_taxonomy = Mock()
        mock_ws.get_table.side_effect = RuntimeError("Table generation failed")
        
        with pytest.raises(RuntimeError, match="Table generation failed"):
            self.reporter.output(mock_ws, self.output, mock_taxonomy)
    
    def test_handle_with_print_error(self):
        """handle should handle print function errors"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = "test"
        mock_cell.value = mock_value
        
        with patch('builtins.print', side_effect=IOError("Print failed")):
            with pytest.raises(IOError, match="Print failed"):
                self.reporter.handle(mock_cell, self.output)
    
    def test_handle_large_indent_values(self):
        """handle should handle large indent values"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = "test"
        mock_cell.value = mock_value
        
        # Should handle large indent without crashing
        with patch('builtins.print'):
            self.reporter.handle(mock_cell, self.output, indent=100)
        
        # Should produce correct number of spaces (200 = 100 * 2)
        output_content = self.output.getvalue()
        assert len(output_content) == 200
        assert output_content == " " * 200
    
    def test_handle_negative_indent(self):
        """handle should handle negative indent values"""
        from ixbrl_reporter.table import Cell
        
        mock_cell = Mock(spec=Cell)
        mock_value = Mock()
        mock_value.value = "test"
        mock_cell.value = mock_value
        
        # Negative indent should result in no spaces (or empty output)
        with patch('builtins.print'):
            self.reporter.handle(mock_cell, self.output, indent=-1)
        
        # Python's "  " * -1 returns empty string
        output_content = self.output.getvalue()
        assert output_content == ""