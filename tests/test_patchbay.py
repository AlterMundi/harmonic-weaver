from __future__ import annotations

import re

import pytest


fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from harmonic_weaver.server import create_app

from engine_fixtures import ready_engine


def test_patchbay_and_offline_assets_are_served_by_the_stage_app() -> None:
    engine, _recorder, _source, _instrument = ready_engine()

    with TestClient(create_app(engine)) as client:
        page = client.get("/")
        alias = client.get("/patchbay")
        script = client.get("/static/patchbay.js")
        styles = client.get("/static/patchbay.css")

    assert page.status_code == alias.status_code == 200
    assert page.text == alias.text
    assert "Harmonic Weaver Patchbay" in page.text
    assert 'id="panic-button"' in page.text
    assert script.status_code == styles.status_code == 200
    assert "new WebSocket" in script.text
    assert "panic_generation" in script.text
    assert "expected_stage_revision" in script.text
    assert "https://" not in page.text
    assert "http://" not in page.text
    assert not re.findall(r'<(?:script|link)[^>]+(?:src|href)="//', page.text)
