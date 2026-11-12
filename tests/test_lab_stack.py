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
            args=types.SimpleNamespace(state_dir=Path(td),spatializer_dir=Path(td),hours=0,with_weaver=False)
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
