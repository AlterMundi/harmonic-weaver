import pytest

from harmonic_weaver.lab.__main__ import main


def test_no_audio_cannot_claim_to_disable_an_external_service(monkeypatch,capsys):
    monkeypatch.setattr('sys.argv',['weaver-lab','--no-audio','--external-shaper'])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code==2
    assert 'cannot disable audio in an external service' in capsys.readouterr().err
