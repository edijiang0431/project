"""Calendar windows retain missing survey quarters rather than backfilling."""
from .contracts import period_key


def latest_four_calendar_quarters(available_periods):
    available = set(available_periods)
    if not available:
        raise ValueError('No available survey quarters')
    last = max(map(period_key, available))
    window = tuple(f'{n // 4:04}_{n % 4 + 1}Q' for n in range(last - 3, last + 1))
    return [p for p in window if p in available], window
