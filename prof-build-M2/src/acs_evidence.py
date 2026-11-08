"""Optional ACS audience-size proxy; never estimates remittance participation."""
import math
import pandas as pd

ACS_SOURCE = 'ACS community-size proxy'
SOURCE_URL = 'https://data.census.gov/table/ACSDT5Y2024.B05006?g=050XX00US06037'
LIMITATION = ('ACS 2020–2024 estimates describe foreign-born residents of Los Angeles County, '
              'not remittance senders, CHIRLA members or campaign need. Margins of error are '
              '90% confidence margins. Small estimates may be imprecise; missing matches stay unavailable. '
              'This geography and period differ from the national quarterly price survey.')


def community_size_rating(estimate, total):
    """0–5 encoding of share of ALL county foreign-born residents, not displayed countries."""
    if not all(math.isfinite(v) for v in (estimate, total)) or total <= 0 or not 0 <= estimate <= total:
        raise ValueError('Expected a nonnegative estimate no larger than a positive county total')
    return 5 * estimate / total


def acs_relevance(details, valid_destination_codes):
    """Convert prepared, auditable ACS rows into the existing evidence contract."""
    from .load_relevance import validate_relevance
    records = []
    for row in details.itertuples(index=False):
        if row.destination_code not in valid_destination_codes or row.match_status != 'Matched':
            continue
        if pd.isna(row.population_estimate) or pd.isna(row.margin_of_error):
            continue
        rating = community_size_rating(row.population_estimate, row.county_foreign_born_total)
        rationale = (f'ACS community-size proxy, not assessed community need. Los Angeles County, '
                     f'2020–2024: {row.acs_category}; estimate {row.population_estimate:g}, '
                     f'90% MOE +/-{row.margin_of_error:g}; county foreign-born total '
                     f'{row.county_foreign_born_total:g} (MOE +/-{row.county_total_margin_of_error:g}). '
                     f'Rating = 5 * estimate / county foreign-born total = {rating:.12g}; '
                     'the score divides this by 5 to recover the population share. '
                     'Point-estimate proxy; uncertainty is not propagated into the composite score. '
                     'Neither the denominator nor the rating depends on displayed destinations.')
        records.append(dict(destination_code=row.destination_code, relevance_rating=rating,
                            rationale=rationale, evidence_source=f'US Census Bureau, ACS 2024 5-year B05006; {row.acs_variable}; {SOURCE_URL}',
                            evidence_date=row.retrieved_date))
    return validate_relevance(pd.DataFrame(records, columns=['destination_code', 'relevance_rating', 'rationale', 'evidence_source', 'evidence_date']), valid_destination_codes)
