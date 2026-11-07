"""Notebook orchestration with a separate last-successful result and guarded export."""
from IPython.display import HTML, display, clear_output
import matplotlib.pyplot as plt
from .contracts import *
from .calculate_summaries import calculate_summaries, input_snapshot, metadata_snapshot, build_cost_reference
from .filter_data import filter_quotes
from .load_relevance import validate_relevance
from .present_results import present_results
from .export_briefing import export_briefing

class NotebookSession:
    def __init__(self,quotes,preparation):
        validate_choices(quotes)
        self.quotes=quotes
        self.preparation=preparation
        self.last_successful_results=None
        self.current_run_valid=False

    def validate_inputs(self,periods,destinations,amount,weights,relevance):
        validate_amount_weights(amount,weights)
        rp,rd=resolve_choices(self.quotes,periods,destinations)
        rel=validate_relevance(relevance,set(self.quotes.destination_code))
        return rp,rd,rel

    def analyze(self,periods,destinations,amount,weights,relevance,provider_preview_rows=100,calendar_window=()):
        clear_output(wait=False); plt.close('all')
        self.current_run_valid=False
        try:
            rp,rd,rel=self.validate_inputs(periods,destinations,amount,weights,relevance)
            filtered=filter_quotes(self.quotes,rp,[d.destination_code for d in rd])
            results=calculate_summaries(filtered,amount,rel,weights,list(periods),list(destinations),rp,rd,self.preparation,available_periods=tuple(sorted(self.quotes.period.unique(),key=period_key)),cost_reference=build_cost_reference(self.quotes,rp,amount))
            if calendar_window:
                from .period_presets import latest_four_calendar_quarters
                expected_periods, expected_window = latest_four_calendar_quarters(self.quotes.period.unique())
                if tuple(calendar_window) != expected_window or set(periods) != set(expected_periods):
                    raise ValueError('Calendar preset disagrees with the latest four-quarter window')
                from dataclasses import replace
                results = replace(results, metadata=replace(results.metadata, calendar_window=tuple(calendar_window)))
            present_results(results,provider_preview_rows)
            self.last_successful_results=results
            self.current_run_valid=True
            return results
        except (ValueError,TypeError) as e:
            display(HTML('<p>Analysis failed; previous displays and export are cleared. Rerun successfully after correcting the inputs.</p>'))
            raise ValueError(str(e)) from e

    def export(self,periods,destinations,amount,weights,relevance,output_dir='exports',calendar_window=()):
        message='Export blocked. Rerun the analysis successfully with the current executed inputs.'
        if self.last_successful_results is None or not self.current_run_valid:
            raise ValueError(message)
        try:
            _,_,rel=self.validate_inputs(periods,destinations,amount,weights,relevance)
            snapshot=input_snapshot(periods,destinations,amount,weights,rel,self.preparation,calendar_window=calendar_window)
        except (ValueError,TypeError) as e:
            raise ValueError(message+' '+str(e)) from e
        if snapshot!=metadata_snapshot(self.last_successful_results.metadata):
            raise ValueError(message)
        return export_briefing(self.last_successful_results,output_dir)
