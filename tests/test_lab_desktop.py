"""Local activation contracts without browser, camera, audio or motor access."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('lab_desktop',Path(__file__).resolve().parents[1]/'scripts/open-harmonic-lab.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class LocalDesktopTests(unittest.TestCase):
    def test_missing_guitar_and_unselected_input_do_not_block_body(self):
        with tempfile.TemporaryDirectory() as td,patch.object(module.Path,'home',return_value=Path(td)),patch.object(module,'configuration',return_value={'guitar':False,'audio':False,'body':True}),patch.object(module,'ensure_panel') as panel,patch.object(module,'ensure_component',return_value='started') as start,patch('sys.argv',['launcher','--no-browser','harmonic-lab://all']):
            module.main();panel.assert_not_called();start.assert_called_once_with('body')
            record=json.loads((Path(td)/'.local/state/harmonic-lab/launch-current.json').read_text())
            self.assertEqual(record['components']['guitar']['status'],'not-selected')
            self.assertEqual(record['components']['body']['status'],'started')
    def test_failed_audio_still_attempts_selected_body_without_restarting_others(self):
        def component(name):
            if name=='audio':raise RuntimeError('Selected input missing')
            return 'reused'
        with tempfile.TemporaryDirectory() as td,patch.object(module.Path,'home',return_value=Path(td)),patch.object(module,'configuration',return_value={'guitar':False,'audio':True,'body':True}),patch.object(module,'ensure_component',side_effect=component),patch('sys.argv',['launcher','--no-browser','harmonic-lab://all']):
            with self.assertRaises(RuntimeError):module.main()
            record=json.loads((Path(td)/'.local/state/harmonic-lab/launch-current.json').read_text())
            self.assertEqual(record['components']['audio']['status'],'unavailable')
            self.assertEqual(record['components']['body']['status'],'reused')
    def test_receiving_profile_accepts_selected_native_audio_only(self):
        with tempfile.TemporaryDirectory() as td,patch.object(module.Path,'home',return_value=Path(td)),patch.dict(module.os.environ,{}):
            root=Path(td);p=root/'.config/harmonic-lab/launch.json';p.parent.mkdir(parents=True)
            p.write_text(json.dumps({'services':{'guitar':False,'audio':False,'body':True},'environment':{'HARMONIC_LAB_AUDIO_BACKEND':'native','HARMONIC_SHAPER_DEVICE':'Headphones'}}))
            self.assertEqual(module.configuration(root)['guitar'],False)
            self.assertEqual(module.os.environ['HARMONIC_SHAPER_DEVICE'],'Headphones')
            p.write_text(json.dumps({'environment':{'PATH':'unsupported'}}))
            with self.assertRaises(ValueError):module.configuration(root)
