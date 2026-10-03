"""Synthetic R01 saved-window/horizon controls. No private observations."""
import argparse
import json
from pathlib import Path
from harmonic_weaver.lab.cache import atomic_json,sha256_file
from harmonic_weaver.lab.research.grassmann import Settings,run
from harmonic_weaver.lab.research.service import ResearchService


def experiment(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    settings=Settings(samples=100,dimensions=4,signal_rank=2,components=2,
                      noise_threshold=.0001,seed=17).model_dump()
    ids=['a'*32,'b'*32,'c'*32]
    comparisons=[]
    manifests=[]
    for repetition in ('first','repeat'):
        service=ResearchService(output/repetition)
        reports=[]
        for ident,change in zip(ids,[{}, {'window_s':.5}, {'horizon_steps':6}]):
            folder=service.root/ident
            report=run({**settings,**change},folder)
            atomic_json(folder/'request.json',report['settings']);reports.append(report)
        cases={}
        for name,selection,support in [('window',[ids[0],ids[1]],'origin_target'),
                ('horizon_pairs',[ids[0],ids[2]],'origin_target'),
                ('horizon_targets',[ids[0],ids[2]],'target')]:
            compared=service.compare({'run_ids':selection,'support':support})
            assert service.compare({'run_ids':selection,'support':support})==compared
            cases[name]=compared
        comparisons.append(cases);manifests.append(reports)
    assert {name:report['controls'] for name,report in comparisons[0].items()}=={
            name:report['controls'] for name,report in comparisons[1].items()}
    assert [r['artifact_hashes'] for r in manifests[0]]==[r['artifact_hashes'] for r in manifests[1]]
    return {'kind':'r01_saved_comparison_controls','recipe_sha256':sha256_file(Path(__file__)),
        'settings':[r['settings'] for r in manifests[0]],
        'cases':{name:{'support_mode':report['support_mode'],'support_columns':report['support_columns'],
                      'controls':report['controls']} for name,report in comparisons[0].items()},
        'input_hashes':manifests[0][0]['input_hashes'],
        'artifact_hashes':[r['artifact_hashes'] for r in manifests[0]],
        'numerical_controls_and_trace_hashes_repeat_identical':True,
        'comparison_code_sha256':comparisons[0]['window']['comparison_code_sha256'],
        'comparison_environment':comparisons[0]['window']['comparison_environment'],
        'producer_code_sha256':manifests[0][0]['code']['code_sha256'],
        'producer_packages':manifests[0][0]['code']['packages'],
        'limits':comparisons[0]['window']['limits']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(experiment(args.output),indent=2,sort_keys=True,allow_nan=False))
