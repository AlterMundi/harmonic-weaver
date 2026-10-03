"""Public R12 software controls; no measured physiological observations."""
import argparse,json
from pathlib import Path
from harmonic_weaver.lab.cache import atomic_json
from harmonic_weaver.lab.research.physiology_sensitivity_run import run,verify


def fixture():
    return {'measurements':{'provider':'synthetic','source_id':'clock-control','subject_slot':'software-slot',
        'task':'Synthetic linear HR and constant declared mechanical power','constraints':'No participant or sensor',
        'clock':{'source_clock':'synthetic','common_clock':'fixture','offset_s':0.,'rate':1.,'uncertainty_s':.5,'method':'declared_assumption'},
        'channels':[{'id':'hr','kind':'heart_rate','units':'bpm','sensor_or_method':'synthetic','uncertainty_description':'Constructed exact values'},
            {'id':'power','kind':'mechanical_power','units':'W','sensor_or_method':'synthetic','uncertainty_description':'Constructed exact values','calibration_evidence_id':'synthetic'}],
        'samples':[{'index':i,'source_time_s':float(i),'values':{'hr':60.+10*i,'power':2.}} for i in range(5)],
        'trials':[{'id':'control','condition':'synthetic','start_s':.5,'end_s':3.5,'outcome_units':'count','outcome_method':'No observed outcome'}],
        'max_gap_s':2.,'common_channel_ids':['hr','power']},'offset_deltas_s':[-.5,0,.5]}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    evidence=[]
    for gap in (False,True):
        request=fixture()
        if gap:
            request['measurements']['samples'][2]['values']['hr']=None
            request['measurements']['samples'][2]['missing_causes']={'hr':'synthetic_sensor_gap'}
        outputs=[]
        for repeat in range(2):
            folder=args.output/f'{"gap" if gap else "linear"}-{repeat}'
            run(request,folder);verify(folder);outputs.append(json.loads((folder/'result.json').read_text()))
        assert outputs[0]==outputs[1]
        evidence.append({'case':'gap' if gap else 'linear','exact_repeat':True,
            'common_support_intervals_s':outputs[0]['common_support_intervals_s'],
            'paired_hr_means':[c['paired_trials'][0]['channels'][0]['mean'] for c in outputs[0]['conditions']]})
    atomic_json(args.output/'evidence.json',{'synthetic_only':True,'cases':evidence})
    print(json.dumps(evidence,indent=2))


if __name__=='__main__':main()
