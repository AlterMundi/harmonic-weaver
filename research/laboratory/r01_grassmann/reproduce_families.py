"""Recompute synthetic family comparisons; compare numbers, not environment digests."""
import argparse
import json
from pathlib import Path
import numpy as np
from harmonic_weaver.lab.research.grassmann import run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--evidence',type=Path,default=Path(__file__).with_name('evidence-families-2026-10-03.json'))
    args=parser.parse_args();evidence=json.loads(args.evidence.read_text())
    for name,expected in evidence['runs'].items():
        result=run(expected['settings'],args.output/name)
        assert result['paired']['common_samples']==expected['paired']['common_samples']
        for control,metrics in expected['paired']['results'].items():
            actual=result['paired']['results'][control]
            assert actual['common_samples']==metrics['common_samples']
            for family,error in metrics['mean_prediction_mse'].items():
                np.testing.assert_allclose(actual['mean_prediction_mse'][family],error,rtol=1e-8,atol=1e-11)
            np.testing.assert_allclose(actual['mean_reconstruction_residual'],metrics['mean_reconstruction_residual'],rtol=1e-8,atol=1e-11)
        print(f'{name}: common support and numerical summaries reproduced')


if __name__=='__main__':main()
