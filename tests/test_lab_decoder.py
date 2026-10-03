"""Optional integration test against the actual worker's video decoder."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_worker_preserves_ffprobe_pts_and_decodes_every_frame(tmp_path):
    python = Path(os.environ.get("HARMOCAP_VENV", Path.home() / "Projects/HarMoCAP/.venv")) / "bin/python"
    if not python.exists() or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("requires HarMoCAP worker environment and ffmpeg")
    probe = subprocess.run([str(python), "-c", "import av"], capture_output=True)
    if probe.returncode:
        pytest.skip("install av in the HarMoCAP worker environment")
    video = tmp_path / "vfr.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=160x120:rate=10",
                    "-frames:v", "4", "-vf", "setpts=if(eq(N\\,0)\\,0\\,if(eq(N\\,1)\\,0.1/TB\\,if(eq(N\\,2)\\,0.4/TB\\,0.7/TB)))",
                    "-fps_mode", "vfr", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)], check=True)
    expected = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
                         "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(video)]))
    times = [float(f["best_effort_timestamp_time"]) for f in expected["frames"]]
    worker = Path(__file__).resolve().parents[1] / "src/harmonic_weaver/lab/perception_worker.py"
    code = """
import importlib.util,json,sys
s=importlib.util.spec_from_file_location('worker',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
frames=list(m.file_frames(sys.argv[2]));print(json.dumps([metadata for image,metadata in frames]))
"""
    actual = json.loads(subprocess.check_output([str(python), "-c", code, str(worker), str(video)]))
    assert [f["source_time_s"] for f in actual] == pytest.approx(times)
    assert len(actual) >= 3 and all(f["timestamp_origin"] == "pts" for f in actual)
    assert len({round(b-a, 4) for a, b in zip(times, times[1:])}) > 1
