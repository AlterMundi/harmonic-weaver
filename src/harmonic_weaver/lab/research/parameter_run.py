"""Persist the experimental R05 amplitude-mapping arm using the shared writer."""
from .parameter_render import Render
from .resonator_run import persist


def run(document, request, folder):
    if set(request)-{'carriers','mapping','render'}:
        raise ValueError('Unknown mapping request field')
    render=Render(document,request.get('carriers',{}),request.get('mapping',{}),request.get('render',{}))
    modules=['parameter_run.py','parameter_render.py','resonator_run.py','resonators.py',
             'resonator_render.py','event_candidates.py','candidate_input.py']
    return persist(document,request,folder,render,render.carriers,modules)
