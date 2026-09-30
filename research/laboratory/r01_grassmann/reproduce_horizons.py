"""Reproduce the frozen synthetic horizon evidence; never reads body media."""
import argparse
import json
from pathlib import Path

from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.research import grassmann


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,default=Path(__file__).with_name('evidence-horizons-2026-09-30.json'))
    args=parser.parse_args()
    evidence=json.loads(args.evidence.read_text())
    if sha256_file(Path(grassmann.__file__))!=evidence['module_sha256']:
        raise ValueError('Estimator code differs from frozen evidence; use its pinned revision')
    for horizon,expected in evidence['runs'].items():
        report=grassmann.run(expected['settings'],args.output/horizon)
        if report['input_hashes']!=expected['input_hashes']:
            raise ValueError(f'Synthetic inputs differ for horizon {horizon}')
        if report['artifact_hashes']!=expected['artifact_hashes']:
            raise ValueError(f'Traces differ for horizon {horizon}; inspect code/package/platform identity')
        print(f'Horizon {horizon}: exact input and trace hashes reproduced')


if __name__=='__main__':main()
