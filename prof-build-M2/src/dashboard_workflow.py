"""Jupyter-free orchestration around the existing analytical contracts."""
from dataclasses import replace
from .dashboard_presentation import COMMUNITY_MODE, validate_mode_weights
from .contracts import period_key, resolve_choices, validate_amount_weights, validate_choices
from .calculate_summaries import calculate_summaries, input_snapshot, metadata_snapshot, build_cost_reference
from .filter_data import filter_quotes
from .load_relevance import validate_relevance
from .export_briefing import export_briefing


class DashboardSession:
    def __init__(self, quotes, preparation):
        validate_choices(quotes)
        self.quotes = quotes
        self.preparation = preparation
        self.last_successful_results = None
        self.current_run_valid = False

    def validate_inputs(self, periods, destinations, amount, weights, relevance, scoring_mode=COMMUNITY_MODE):
        validate_mode_weights(scoring_mode, weights)
        validate_amount_weights(amount, weights)
        rp, rd = resolve_choices(self.quotes, periods, destinations)
        rel = validate_relevance(relevance, set(self.quotes.destination_code))
        return rp, rd, rel

    def analyze(self, periods, destinations, amount, weights, relevance, scoring_mode=COMMUNITY_MODE, calendar_window=()):
        self.current_run_valid = False
        rp, rd, rel = self.validate_inputs(periods, destinations, amount, weights, relevance, scoring_mode)
        filtered = filter_quotes(self.quotes, rp, [d.destination_code for d in rd])
        results = calculate_summaries(
            filtered, amount, rel, weights, list(periods), list(destinations),
            rp, rd, self.preparation,
            available_periods=tuple(sorted(self.quotes.period.unique(), key=period_key)),
            cost_reference=build_cost_reference(self.quotes, rp, amount),
        )
        if calendar_window:
            from .period_presets import latest_four_calendar_quarters
            expected_periods, expected_window = latest_four_calendar_quarters(self.quotes.period.unique())
            if tuple(calendar_window) != expected_window or set(periods) != set(expected_periods):
                raise ValueError('Calendar preset disagrees with the latest four-quarter window')
        results = replace(results, metadata=replace(results.metadata, scoring_mode=scoring_mode, calendar_window=tuple(calendar_window)))
        self.last_successful_results = results
        self.current_run_valid = True
        return results

    def matches(self, periods, destinations, amount, weights, relevance, scoring_mode=COMMUNITY_MODE, calendar_window=()):
        if not self.current_run_valid or self.last_successful_results is None:
            return False
        try:
            _, _, rel = self.validate_inputs(periods, destinations, amount, weights, relevance, scoring_mode)
            return input_snapshot(periods, destinations, amount, weights, rel, self.preparation, scoring_mode, calendar_window) == metadata_snapshot(self.last_successful_results.metadata)
        except (ValueError, TypeError):
            return False

    def export(self, periods, destinations, amount, weights, relevance, output_dir='exports', scoring_mode=COMMUNITY_MODE, calendar_window=()):
        if not self.matches(periods, destinations, amount, weights, relevance, scoring_mode, calendar_window):
            raise ValueError('Export blocked. Update analysis successfully with the current settings and community evidence.')
        return export_briefing(self.last_successful_results, output_dir)
