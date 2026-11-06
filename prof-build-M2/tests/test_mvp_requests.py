"""Acceptance checks for the team's Module 9 change requests."""
import pandas as pd
import pytest

from src.contracts import RELEVANCE, ScoringWeights
from src.dashboard_presentation import COST_MODE
from src.dashboard_workflow import DashboardSession
from src.rendering import access_checklist_html


def test_cr01_access_checklist():
    text = access_checklist_html()
    assert 'reliable Internet' in text and 'secure connection' in text
    assert 'not facts inferred' in text and 'no personal answers' in text
