import pytest
from harmonic_weaver.lab.research.experience_pair_design import preview
from harmonic_weaver.lab.research.experience_pair_design_presets import PairDesignPresets
from harmonic_weaver.lab.research.experience_response_service import ResponseService
from harmonic_weaver.lab.research.experience_service import ExperienceService
from harmonic_weaver.lab.research.experience_transport_service import TransportService
from harmonic_weaver.lab.research.experience_protocol import schedule
from harmonic_weaver.lab.cache import sha256_file
from test_experience_protocol import data


def test_portable_direction_design_missing_support_and_restart(tmp_path):
    protocols=ExperienceService(tmp_path);responses=ResponseService(tmp_path);transports=TransportService(tmp_path)
    p=protocols.start({'protocol':data()});pid=p['id'];digest=sha256_file(protocols.artifact(pid,'manifest.json'))
    ids=[]
    for trial in ('trial-0001','trial-0003'):
        ids.append(responses.start(protocols,transports,{'protocol_id':pid,'protocol_manifest_sha256':digest,
            'response':{'trial_id':trial,'ratings':{i['id']:None for i in schedule(data())['request']['config']['items']}}})['id'])
    config={'contrasts':[{'reference_condition':'video_only','target_condition':'audiovisual'},
                        {'reference_condition':'video_only','target_condition':'sound_only'}]}
    result=preview(responses,{'response_ids':ids,'config':config})
    assert result==preview(responses,{'response_ids':ids,'config':config})
    assert result['pairs']==[{'reference_id':ids[0],'target_id':ids[1]}]
    assert result['missing'][0]['target_id'] is None and result['missing'][0]['reference_id']==ids[0]
    presets=PairDesignPresets(tmp_path);saved=presets.save({'name':'portable','config':config})
    assert PairDesignPresets(tmp_path).load(saved['id']).config.model_dump()==config
    for key in ('participant_slot','response_ids','calibration','sources'):
        with pytest.raises(ValueError):presets.save({'name':'bad','config':{**config,key:'private'}})
    with pytest.raises(ValueError):presets.save({'name':'bad','config':{'contrasts':[config['contrasts'][0]]*2}})
