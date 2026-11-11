"""Hardware-free contract and routing checks; fixtures are not physical audio evidence."""
import io
import unittest
from unittest.mock import patch

from harmonic_weaver.drivers.guitar_spectrum import GuitarSpectrumSource, source_manifest
from harmonic_weaver.engine import WeaverEngine
from engine_fixtures import instrument_manifest, safety_profile, route, scene


def snapshot():
    return {'source_schema':'hbg.spectrum/v1','stream_id':'0000000000000001',
            'sample_seq':1,'sample_age_ms':10,'running':True,'error':None,
            'latest':{'rms_db':-24.0,'clipped':False,'peaks':[{'hz':440.0}]}}


class GuitarSpectrumTests(unittest.TestCase):
    def setUp(self):
        self.engine=WeaverEngine();self.source=GuitarSpectrumSource(self.engine)
        self.addCleanup(self.engine.close)

    def value(self,name):
        return self.engine.source_value('guitar-spectrum.'+name)

    def test_contract_and_exact_values(self):
        m=source_manifest();self.assertEqual(len(m['channels']),3)
        self.assertTrue(self.source.consume(snapshot()))
        self.assertEqual(self.value('peak_hz').value,440)
        self.assertEqual(self.value('rms_db').value,-24)
        self.assertEqual(self.value('clipped').value,0)
        self.assertEqual(self.value('peak_hz').state,'observed')

    def test_duplicate_does_not_renew_observation_then_stale_invalidates(self):
        s=snapshot();self.source.consume(s)
        before=self.value('peak_hz')
        self.assertFalse(self.source.consume(s));self.assertIs(self.value('peak_hz'),before)
        s['sample_age_ms']=251;self.source.consume(s)
        self.assertEqual(self.value('peak_hz').state,'invalid')

    def test_stopped_error_silence_and_request_latency(self):
        for key,value in [('running',False),('error','capture ended'),('sample_age_ms',500)]:
            self.source.consume(snapshot());s=snapshot();s[key]=value;self.source.consume(s)
            self.assertEqual(self.value('rms_db').state,'invalid')
        s=snapshot();s['sample_seq']=2;s['latest']['peaks']=[];self.source.consume(s)
        self.assertEqual(self.value('peak_hz').state,'invalid')
        self.assertEqual(self.value('rms_db').state,'observed')
        s['sample_seq']=3;self.source.consume(s,transit_ms=250)
        self.assertEqual(self.value('rms_db').state,'invalid')

    def test_legacy_malformed_and_nonfinite_invalidates_all(self):
        for mutate in (lambda s:s.pop('source_schema'),lambda s:s.update(stream_id='bad'),
                       lambda s:s['latest'].update(rms_db=float('nan')),
                       lambda s:s['latest'].update(clipped=1),lambda s:s.update(sample_seq=True)):
            s=snapshot();mutate(s)
            with self.assertRaises((ValueError,TypeError)):self.source.consume(s)
            for name in ('peak_hz','rms_db','clipped'):self.assertEqual(self.value(name).state,'invalid')

    def test_restart_and_nonmonotonic_sample_identity(self):
        s=snapshot();s['sample_seq']=8;self.source.consume(s)
        s['sample_seq']=7
        with self.assertRaises(ValueError):self.source.consume(s)
        old=self.source.stream;s['stream_id']='0000000000000002';s['sample_seq']=1
        self.assertTrue(self.source.consume(s));self.assertNotEqual(self.source.stream,old)
        self.assertEqual(self.value('peak_hz').state,'observed')

    def test_existing_router_handshake_and_native_output(self):
        # Use the maintained engine and native instrument contract. Recorder only:
        # this asserts actual routing code, not UDP delivery or synthesis/audio.
        instrument=instrument_manifest();self.engine.install_instrument(instrument,safety_profile(instrument))
        transforms=[{'type':'scale_range','in':[-160,0],'out':[0,1],'clamp':True}]
        self.engine.upsert_scene(scene(routes=[route(channel='guitar-spectrum.rms_db',transforms=transforms)]),self.engine.stage_revision)
        self.engine.switch_scene('main',1,self.engine.stage_revision)
        self.source.consume(snapshot())
        self.assertEqual(self.engine.transport.records,[])
        self.engine.instrument_hello('synth','0000000000000002',instrument['contract_id'])
        self.engine.instrument_sync_complete('synth','0000000000000002',instrument['contract_id'])
        s=snapshot();s['sample_seq']=2;self.source.consume(s)
        self.assertAlmostEqual(self.engine.transport.records[-1].value,.85)

    def test_read_is_one_bounded_get_and_failure_invalidates(self):
        import json
        response=io.BytesIO(json.dumps(snapshot()).encode())
        with patch('harmonic_weaver.drivers.guitar_spectrum.build_opener') as make:
            make.return_value.open.return_value=response
            self.assertTrue(self.source.poll_once())
            make.return_value.open.assert_called_once_with('http://127.0.0.1:18879/audio/state',timeout=2)
        with patch('harmonic_weaver.drivers.guitar_spectrum.build_opener') as make:
            make.return_value.open.side_effect=OSError('not listening')
            with self.assertRaises(OSError):self.source.poll_once()
            self.assertEqual(self.value('peak_hz').state,'invalid')

    def test_oversize_and_redirect_are_not_followed(self):
        from harmonic_weaver.drivers.guitar_spectrum import NoRedirect
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,None,None,None,None)
        with patch('harmonic_weaver.drivers.guitar_spectrum.build_opener') as make:
            make.return_value.open.return_value=io.BytesIO(b' '*65537)
            with self.assertRaisesRegex(ValueError,'64KiB'):self.source.poll_once()
        self.assertEqual(self.value('peak_hz').state,'invalid')
