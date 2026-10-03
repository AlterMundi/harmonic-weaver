"""Past-only direct forecasts; fixed hyperparameters, no held-out tuning."""
from typing import Literal
import numpy as np

Predictor = Literal['persistence','full_ridge','subspace_ridge','linear_trend',
                    'lagged_full_ridge','lagged_subspace_ridge']
DEFAULT_PREDICTORS = ['persistence','full_ridge','subspace_ridge']


def linear_trend(past, horizon):
    clock = np.arange(len(past),dtype=float)
    centered = clock-clock.mean()
    slope = centered @ past / (centered @ centered)
    return past.mean(axis=0)+(clock[-1]+horizon-clock.mean())*slope


def lagged_ridge(past,basis,ridge,horizon,lags):
    # Each fit pair is (q consecutive past vectors, vector h steps later).
    # The latest target is past[-1]; no observation beyond origin enters fit.
    z = past @ basis
    origins = range(lags-1,len(past)-horizon)
    x = np.stack([z[i-lags+1:i+1].reshape(-1) for i in origins])
    y = z[lags-1+horizon:]
    mx,my = x.mean(axis=0),y.mean(axis=0)
    coefficients = np.linalg.solve((x-mx).T@(x-mx)+ridge*np.eye(x.shape[1]),(x-mx).T@(y-my))
    # Keep the mean of the target's full coordinates, including complement.
    mean_target = past[lags-1+horizon:].mean(axis=0)
    return mean_target+((z[-lags:].reshape(-1)-mx)@coefficients)@basis.T
