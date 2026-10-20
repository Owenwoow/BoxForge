"""Headless Streamlit run of the web UI: the default page must build and
render a model without raising or showing an error box."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

APP = Path(__file__).resolve().parents[1] / "box_generator" / "app.py"


def test_app_renders_default_model():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(APP), default_timeout=300).run()

    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]
    # Size / volume / validity metrics only appear once a solid was built.
    assert len(at.metric) == 3
