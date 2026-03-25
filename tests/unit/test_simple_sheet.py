"""
Unit tests for ixbrl_reporter.simple_sheet module

Tests for suppress-if-zero and is_all_zero functionality.
"""
import pytest
from unittest.mock import Mock
from datetime import date

from ixbrl_reporter.simple_sheet import SimpleWorksheet, is_all_zero
from ixbrl_reporter.computation import Group
from ixbrl_reporter.table import Index, TotalIndex, Row


def make_computation(value_per_period, suppress_zero=False):
    """Create a mock computation that returns the given value for each period.

    value_per_period: a single value (used for all periods) or a list.
    Values cycle so the mock can be called multiple times (e.g. by
    is_all_zero and then again by cell creation).
    """
    if not isinstance(value_per_period, list):
        value_per_period = [value_per_period]

    comp = Mock()
    comp.metadata.suppress_zero = suppress_zero
    comp.metadata.note = None

    call_count = [0]

    def make_output(result):
        out = Mock()
        datum = Mock()
        datum.value = value_per_period[call_count[0] % len(value_per_period)]
        call_count[0] += 1
        out.value = datum
        return out

    comp.get_output.side_effect = make_output
    return comp


def make_results(n_periods=2):
    """Create a list of (period, result) tuples."""
    return [(Mock(), Mock()) for _ in range(n_periods)]


class TestIsAllZero:
    """Test the is_all_zero helper function"""

    def test_all_zero_single_period(self):
        comp = make_computation([0])
        results = make_results(1)
        assert is_all_zero(comp, results) is True

    def test_all_zero_multiple_periods(self):
        comp = make_computation([0, 0])
        results = make_results(2)
        assert is_all_zero(comp, results) is True

    def test_not_all_zero_one_nonzero(self):
        comp = make_computation([0, 100.0])
        results = make_results(2)
        assert is_all_zero(comp, results) is False

    def test_not_all_zero_all_nonzero(self):
        comp = make_computation([50.0, 100.0])
        results = make_results(2)
        assert is_all_zero(comp, results) is False

    def test_negative_value_is_nonzero(self):
        comp = make_computation([0, -1.0])
        results = make_results(2)
        assert is_all_zero(comp, results) is False


class TestSingleLineSuppress:
    """Test suppress-if-zero for single line computations"""

    def setup_method(self):
        self.ws = SimpleWorksheet([], [], Mock())

    def test_suppress_zero_returns_none(self):
        """A zero line with suppress-if-zero should be suppressed"""
        comp = make_computation([0, 0], suppress_zero=True)
        results = make_results(2)

        ix = self.ws.get_single_line_ix(comp, results)
        assert ix is None

    def test_suppress_zero_nonzero_keeps_line(self):
        """A non-zero line with suppress-if-zero should not be suppressed"""
        comp = make_computation([0, 100.0], suppress_zero=True)
        results = make_results(2)

        ix = self.ws.get_single_line_ix(comp, results)
        assert ix is not None
        assert isinstance(ix, Index)

    def test_no_suppress_zero_keeps_line(self):
        """A zero line without suppress-if-zero should not be suppressed"""
        comp = make_computation([0, 0], suppress_zero=False)
        results = make_results(2)

        ix = self.ws.get_single_line_ix(comp, results)
        assert ix is not None


class TestBreakdownSuppress:
    """Test suppress-if-zero for group breakdown computations"""

    def setup_method(self):
        self.ws = SimpleWorksheet([], [], Mock())

    def _make_group(self, inputs, group_value_per_period,
                    suppress_zero=False):
        """Create a mock Group computation with inputs."""
        group = Mock()
        group.metadata.suppress_zero = suppress_zero
        group.metadata.note = None
        group.inputs = inputs

        if not isinstance(group_value_per_period, list):
            group_value_per_period = [group_value_per_period]

        call_count = [0]

        def make_output(result):
            out = Mock()
            datum = Mock()
            datum.value = group_value_per_period[
                call_count[0] % len(group_value_per_period)
            ]
            call_count[0] += 1
            out.value = datum
            return out

        group.get_output.side_effect = make_output
        return group

    def test_suppress_zero_group_all_zero(self):
        """A group with suppress-if-zero where total is zero should return None"""
        child = make_computation([10, 20])
        group = self._make_group([child], [0, 0], suppress_zero=True)

        results = make_results(2)
        ix = self.ws.get_breakdown_ix(group, results)
        assert ix is None

    def test_suppress_zero_group_nonzero_keeps(self):
        """A group with suppress-if-zero where total is non-zero should remain"""
        child = make_computation([10, 20])
        group = self._make_group([child], [10, 20], suppress_zero=True)

        results = make_results(2)
        ix = self.ws.get_breakdown_ix(group, results)
        assert ix is not None

    def test_suppress_zero_child_filtered(self):
        """A zero child with suppress-if-zero should be filtered from group"""
        child_kept = make_computation([100, 200], suppress_zero=False)
        child_suppressed = make_computation([0, 0], suppress_zero=True)

        group = self._make_group(
            [child_kept, child_suppressed], [100, 200]
        )

        results = make_results(2)
        ix = self.ws.get_breakdown_ix(group, results)

        # Should be a group index with heading + 1 child + total = 3 items
        # The outer Index contains child indices
        assert isinstance(ix, Index)
        # child list: 1 kept child + 1 TotalIndex
        children = ix.child
        assert len(children) == 2
        assert isinstance(children[0], Index)
        assert isinstance(children[1], TotalIndex)

    def test_suppress_zero_child_nonzero_kept(self):
        """A non-zero child with suppress-if-zero should remain in group"""
        child = make_computation([0, 100.0], suppress_zero=True)

        group = self._make_group([child], [0, 100.0])

        results = make_results(2)
        ix = self.ws.get_breakdown_ix(group, results)

        children = ix.child
        # 1 child + 1 total
        assert len(children) == 2

    def test_all_children_suppressed_renders_as_single_line(self):
        """When all children are suppressed, group renders as a single line"""
        child1 = make_computation([0, 0], suppress_zero=True)
        child2 = make_computation([0, 0], suppress_zero=True)

        group = self._make_group([child1, child2], [0, 0])

        results = make_results(2)
        ix = self.ws.get_breakdown_ix(group, results)

        # Should look like a single line: Index wrapping a TotalIndex
        assert isinstance(ix, Index)
        assert len(ix.child) == 1
        assert isinstance(ix.child[0], TotalIndex)


class TestGetTableSuppress:
    """Test suppress-if-zero integration in get_table"""

    def test_suppressed_lines_excluded_from_table(self):
        """Suppressed lines should not appear in the table"""
        mock_data = Mock()
        mock_data.get_config.return_value = "£"

        period = Mock()
        period.name = "2020"
        mock_data.get_periods.return_value = [period]

        # Two computations: one kept, one suppressed
        comp_kept = make_computation([100.0], suppress_zero=False)
        comp_kept.metadata.id = "kept"

        comp_suppressed = make_computation([0], suppress_zero=True)
        comp_suppressed.metadata.id = "suppressed"

        mock_data.get_computation.side_effect = lambda id: {
            "kept": comp_kept,
            "suppressed": comp_suppressed,
        }[id]

        result_set = Mock()
        mock_data.perform_computations.return_value = result_set

        ws_elts = [Mock(), Mock()]
        ws_elts[0].id = "kept"
        ws_elts[1].id = "suppressed"

        ws = SimpleWorksheet(ws_elts, [period], mock_data)
        table = ws.get_table(Mock())

        # Only 1 row should remain (the kept one)
        assert len(table.ixs) == 1
