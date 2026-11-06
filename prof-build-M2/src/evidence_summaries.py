"""Pure, non-mutating evidence calculations shared by all report views."""
import numpy as np
import pandas as pd


def channel_cost_comparison(results):
    records = []
    for destination in results.metadata.resolved_destinations:
        rows = results.channel_summary.loc[results.channel_summary.destination_code.eq(destination.destination_code)].set_index('channel_category')
        def value(category, column):
            return rows.loc[category, column] if category in rows.index else np.nan
        internet = value('Internet-only', 'median_total_cost')
        counter = value('Counter-only', 'median_total_cost')
        delta = counter - internet
        direction = ('Unavailable' if pd.isna(delta) else 'Counter-only higher' if delta > 0 else 'Internet-only higher' if delta < 0 else 'Equal medians')
        records.append(dict(destination_code=destination.destination_code, receiving_country=destination.destination_name,
            internet_median_pct=internet, counter_median_pct=counter,
            internet_eligible_quotes=value('Internet-only', 'observations'), counter_eligible_quotes=value('Counter-only', 'observations'),
            counter_minus_internet_percentage_points=delta,
            counter_minus_internet_usd=delta * results.metadata.transfer_amount_usd / 100,
            direction=direction))
    return pd.DataFrame(records, columns=['destination_code','receiving_country','internet_median_pct','counter_median_pct',
        'internet_eligible_quotes','counter_eligible_quotes','counter_minus_internet_percentage_points','counter_minus_internet_usd','direction'])
