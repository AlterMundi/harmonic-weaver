import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('lab_web_agent',Path(__file__).resolve().parents[1]/'laboratory-control/backend/agent.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class AgentTests(unittest.TestCase):
    def test_unknown_operations_and_services_never_spawn(self):
        with tempfile.TemporaryDirectory() as td,patch.object(a,'STATE',Path(td)),patch.object(a.subprocess,'Popen') as start:
            for request in ({'op':'shell'},{'op':'start','service':'../motor','id':'x'},{'op':'start','service':'body','id':'bad/id'}):
                with self.assertRaises(ValueError):a.dispatch(request)
            start.assert_not_called()
    def test_duplicate_request_does_not_spawn_again(self):
        with tempfile.TemporaryDirectory() as td,patch.object(a,'STATE',Path(td)),patch.object(a,'snapshot',return_value={'job':{'id':'same'}}),patch.object(a.subprocess,'Popen') as start:
            (Path(td)/'job.json').write_text(json.dumps({'id':'same','phase':'finished'}))
            a.dispatch({'op':'start','service':'all','id':'same'});start.assert_not_called()
    def test_failed_optional_audio_does_not_block_other_services(self):
        def ensure(name):
            if name=='audio':raise RuntimeError('Selected input missing')
            return 'started'
        m=types.SimpleNamespace(configuration=lambda _:dict(guitar=False,audio=True,body=True),ensure_component=ensure)
        with tempfile.TemporaryDirectory() as td,patch.object(a,'STATE',Path(td)),patch.object(a,'launcher',return_value=m):
            a.worker('request',['guitar','audio','body'])
            job=json.loads((Path(td)/'job.json').read_text())
            self.assertEqual(job['results']['guitar']['status'],'not-selected')
            self.assertEqual(job['results']['audio']['status'],'failed')
            self.assertEqual(job['results']['body']['status'],'started')
    def test_configuration_cannot_change_transport_or_paths(self):
        with tempfile.TemporaryDirectory() as td,patch.object(a,'STATE',Path(td)):
            for profile in ({'environment':{'PATH':'/arbitrary'}},{'services':{'shell':True}},{'command':'id'},{'environment':{'HARMONIC_SHAPER_DEVICE':'a\nb'}}):
                with self.assertRaises(ValueError):a.dispatch({'op':'configure','profile':profile})
