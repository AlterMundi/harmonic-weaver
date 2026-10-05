"""Preflight reservation checks; the real body execution is recorded privately."""
import importlib
from pathlib import Path
from types import SimpleNamespace
import pytest


@pytest.fixture
def recipe(monkeypatch):
    folder=Path(__file__).resolve().parents[2]/'research/laboratory/r07_membrane'
    monkeypatch.syspath_prepend(str(folder))
    return importlib.import_module('reserved_recordings')


def test_subject_identity_is_not_inferred_by_recipe(recipe,tmp_path):
    with pytest.raises(ValueError,match='take reservation'):
        recipe.reproduce(tmp_path,{'reservation':'subject'},tmp_path/'output')
    assert not (tmp_path/'output').exists()


@pytest.mark.parametrize('distinct',[False,True])
def test_recording_overlap_or_insufficient_cases_rejected_before_projection(recipe,monkeypatch,tmp_path,distinct):
    evaluation=SimpleNamespace(ident='a'*32,manifest={'runs':[{},{}]})
    monkeypatch.setattr(recipe,'FrozenEvaluation',lambda _:evaluation)
    monkeypatch.setattr(recipe,'freeze',lambda _,ident,index:index)
    def inspect(index):
        manifest={'source_records':[{'source_index':index,'cache_manifest':{'media_sha256':str(index) if distinct else 'same'}}]}
        return None,manifest,{'source_index':index},None
    monkeypatch.setattr(recipe,'inspect',inspect)
    monkeypatch.setattr(recipe,'project',lambda *a:pytest.fail('must reject before projecting'))
    plan={'reservation':'take','windows':[{'run_index':0,'role':'train'},{'run_index':1,'role':'test'}]}
    reason='three train' if distinct else 'distinct recording'
    with pytest.raises(ValueError,match=reason):recipe.reproduce(tmp_path,plan,tmp_path/'output')
    assert not (tmp_path/'output').exists()
