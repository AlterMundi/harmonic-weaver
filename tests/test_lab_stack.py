import importlib.util
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch,Mock

spec=importlib.util.spec_from_file_location('lab_stack',Path(__file__).resolve().parents[1]/'scripts/harmonic-lab-session.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class StackTests(unittest.TestCase):
    def test_close_terminates_only_owned_process_groups(self):
        stack=module.Stack.__new__(module.Stack)
        child=Mock(pid=123,returncode=0);child.wait.return_value=0
        stack.children={'spatializer':child};stack.borrowed=['guitar','weaver'];stack.lock=Mock()
        with patch.object(module.os,'killpg') as kill:
            stack.close()
            kill.assert_called_once_with(123,module.signal.SIGTERM)
        self.assertEqual(stack.children_exit,{'spatializer':0})
    def test_existing_services_are_reused_and_startup_is_single_owner(self):
        with tempfile.TemporaryDirectory() as td,patch.dict('sys.modules',{'bounded_log':types.SimpleNamespace(copy_tail=lambda *_:None)}):
            args=types.SimpleNamespace(state_dir=Path(td),spatializer_dir=Path(td),hours=0,with_weaver=False,no_guitar_controller=False)
            stack=module.Stack(args)
            try:
                with self.assertRaises(BlockingIOError):module.Stack(args)
                stack.audio_snapshot={'confirmed':'fixture'}
                with patch.object(module,'alive',return_value=True),patch.object(stack,'audio_ready',return_value=True),patch.object(stack,'start') as start:
                    stack.run();start.assert_not_called()
                self.assertEqual(stack.borrowed,['guitar','spatializer'])
            finally:stack.close()

    def test_canonical_live_entry_exposes_the_profile_without_starting_devices(self):
        import subprocess
        command=Path(__file__).resolve().parents[1]/'scripts/start-live-stack.sh'
        result=subprocess.run([str(command),'--guitar-lab','--help'],capture_output=True,text=True,timeout=5,check=True)
        self.assertIn('--with-weaver',result.stdout)

    def test_coreaudio_readiness_does_not_claim_a_jack_graph(self):
        import json
        from engine_fixtures import instrument_manifest
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'spatializer').mkdir()
            (root/'beacon_spatial.contract.json').write_text(json.dumps(instrument_manifest()))
            (root/'spatializer/native.json').write_text(json.dumps({'phase':'processes_started','source':'live','input_device':'Input','output_device':'Output'}))
            stack=module.Stack.__new__(module.Stack);stack.state=root;stack.args=types.SimpleNamespace(spatializer_dir=root)
            with patch.object(module,'alive',return_value=True),patch.object(module.platform,'system',return_value='Darwin'),patch.object(module,'beacon_snapshot',return_value={}),patch.object(module.subprocess,'run') as run,patch.dict(module.os.environ,{'BEACON_INPUT_DEVICE':'Input','BEACON_OUTPUT_DEVICE':'Output'}):
                self.assertTrue(stack.audio_ready());run.assert_not_called()
                self.assertEqual(stack.audio_snapshot['coreaudio_configuration']['input_device'],'Input')
                with patch.dict(module.os.environ,{'BEACON_OUTPUT_DEVICE':'Different'}):self.assertFalse(stack.audio_ready())

    def test_mac_optional_stack_uses_native_audio_without_motor_requirement(self):
        with tempfile.TemporaryDirectory() as td,patch.dict('sys.modules',{'bounded_log':types.SimpleNamespace(copy_tail=lambda *_:None)}):
            args=types.SimpleNamespace(state_dir=Path(td),spatializer_dir=Path(td),hours=0,with_weaver=True,no_guitar_controller=True)
            stack=module.Stack(args);stack.audio_snapshot={}
            try:
                with patch.object(module,'alive',return_value=False),patch.object(module.platform,'system',return_value='Darwin'),patch.object(stack,'wait_ready'),patch.object(stack,'start') as start,patch.dict(module.os.environ,{'BEACON_INPUT_DEVICE':'Input','BEACON_OUTPUT_DEVICE':'Output','HARMONIC_SHAPER_DEVICE':'Native Output'}):
                    stack.run()
                names=[call.args[0] for call in start.call_args_list]
                self.assertEqual(names,['spatializer','weaver'])
                command=start.call_args_list[-1].args[1]
                self.assertIn('native',command);self.assertIn('Native Output',command)
                self.assertIn('auto',command);self.assertNotIn('jack',command)
            finally:stack.close()

    def test_body_component_reuses_existing_launcher_without_touching_audio_or_motor(self):
        with tempfile.TemporaryDirectory() as td,patch.dict('sys.modules',{'bounded_log':types.SimpleNamespace(copy_tail=lambda *_:None)}):
            args=types.SimpleNamespace(state_dir=Path(td),spatializer_dir=Path(td),hours=0,with_weaver=False,no_guitar_controller=False,body_only=True)
            stack=module.Stack(args)
            try:
                with patch.object(module,'alive',return_value=False),patch.object(module.platform,'system',return_value='Linux'),patch.object(stack,'wait_ready'),patch.object(stack,'start') as start:
                    stack.run()
                self.assertEqual([c.args[0] for c in start.call_args_list],['weaver'])
                self.assertIn(str(module.ROOT/'scripts/start-laboratory.sh'),start.call_args.args[1])
            finally:stack.close()

    def test_body_component_accepts_selected_native_output_without_guitar_input(self):
        with tempfile.TemporaryDirectory() as td,patch.dict('sys.modules',{'bounded_log':types.SimpleNamespace(copy_tail=lambda *_:None)}):
            args=types.SimpleNamespace(state_dir=Path(td),spatializer_dir=Path(td),hours=0,with_weaver=False,no_guitar_controller=True,body_only=True)
            stack=module.Stack(args)
            try:
                with patch.object(module,'alive',return_value=False),patch.object(module.platform,'system',return_value='Linux'),patch.object(stack,'wait_ready'),patch.object(stack,'start') as start,patch.dict(module.os.environ,{'HARMONIC_LAB_AUDIO_BACKEND':'native','HARMONIC_SHAPER_DEVICE':'Chosen Output'}):
                    stack.run()
                command=start.call_args.args[1]
                self.assertIn('native',command);self.assertIn('Chosen Output',command);self.assertNotIn('R24 Analog Stereo',command)
            finally:stack.close()
