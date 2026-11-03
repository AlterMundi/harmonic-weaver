"""An updated entry must be visible on the next visit, without live-page reloads."""
import os

import pytest
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.testclient import TestClient

from harmonic_weaver.lab.ui_assets import LaboratoryUIFiles


@pytest.fixture
def ui(tmp_path):
    (tmp_path/'index.html').write_text('<html><body>previous UI</body></html>')
    (tmp_path/'assets').mkdir()
    (tmp_path/'assets/example-v1.js').write_text('console.log("versioned bundle")')
    return tmp_path,TestClient(Starlette(routes=[Mount('/',app=LaboratoryUIFiles(directory=tmp_path,html=True))]))


@pytest.mark.parametrize('url',['/','/index.html','/?mode=face'])
def test_entry_html_is_not_reused_as_a_stale_cached_page(ui,url):
    _,client=ui;response=client.get(url)
    assert response.status_code==200
    assert response.headers['cache-control']=='no-store'


def test_conditional_entry_preserves_no_store_and_an_updated_entry_gets_new_bytes(ui):
    root,client=ui;first=client.get('/')
    same=client.get('/',headers={'If-None-Match':first.headers['etag']})
    assert same.status_code==304 and same.headers['cache-control']=='no-store'
    entry=root/'index.html';old=entry.stat();entry.write_text('<html><body>current UI with face mode</body></html>')
    os.utime(entry,ns=(old.st_atime_ns,old.st_mtime_ns+1_000_000_000))
    updated=client.get('/?mode=face',headers={'If-None-Match':first.headers['etag']})
    assert updated.status_code==200 and 'current UI with face mode' in updated.text
    assert updated.headers['cache-control']=='no-store'


def test_versioned_assets_remain_ordinary_static_resources(ui):
    _,client=ui;response=client.get('/assets/example-v1.js')
    assert response.status_code==200
    assert 'cache-control' not in response.headers
    assert client.get('/assets/example-v1.js',headers={'If-None-Match':response.headers['etag']}).status_code==304
