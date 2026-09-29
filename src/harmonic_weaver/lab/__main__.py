"""Local launcher. Owns only the Shaper child it starts; never kills listeners."""
import argparse
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import time

import httpx
import uvicorn

from .app import create_app
from .audio import ShaperOutput
from .contracts import PerceptionSettings
from .routing import PreparedRoutes
from .presets import seed_presets
from .runtime import LaboratoryRuntime
from .store import SessionStore


def available_port(port):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError as exc:
            raise ValueError(f"127.0.0.1:{port} is occupied; choose another port or explicitly use --external-shaper") from exc


def main():
    parser = argparse.ArgumentParser(description="Laboratorio corporal Weaver (localhost)")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--shaper-port", type=int, default=8085)
    parser.add_argument("--external-shaper", action="store_true")
    parser.add_argument("--shaper-dir", type=Path, default=Path(os.environ.get("SHAPER_DIR", "../harmonic-shaper")))
    parser.add_argument("--shaper-python", default=os.environ.get("SHAPER_PYTHON"))
    parser.add_argument("--device", help="Shaper audio device name or ID")
    parser.add_argument("--audio-backend", choices=("auto", "native", "jack"), default="auto")
    parser.add_argument("--no-audio", action="store_true", help="diagnostic mode; no usable sound")
    parser.add_argument("--checkpoint", default=os.environ.get("HARMOCAP_CHECKPOINT"))
    parser.add_argument("--tracking-device", default="auto")
    parser.add_argument("--data-dir", type=Path, default=Path.home()/".local/share/harmonic-weaver/laboratory")
    parser.add_argument("--ui-dir", type=Path, default=Path(__file__).resolve().parents[3]/"laboratory-ui/dist")
    args = parser.parse_args()
    if not args.checkpoint or not Path(args.checkpoint).expanduser().is_file():
        parser.error("--checkpoint must name an existing local HarMoCAP pose model")
    if not (args.ui_dir/"index.html").is_file():
        parser.error("build laboratory-ui first: cd laboratory-ui && npm ci && npm run build")
    try:
        available_port(args.port)
        if not args.external_shaper:
            available_port(args.shaper_port)
    except ValueError as exc:
        parser.error(str(exc))
    url = f"http://127.0.0.1:{args.shaper_port}"
    child = None
    store = None
    try:
        if not args.external_shaper:
            shaper = args.shaper_dir.expanduser().resolve()
            python = args.shaper_python or str(shaper/".venv/bin/python")
            command = [python, "-m", "harmonic_shaper", "--no-midi", "--no-osc",
                       "--api-host", "127.0.0.1", "--api-port", str(args.shaper_port)]
            jack = args.audio_backend == "jack" or (args.audio_backend == "auto" and shutil.which("pw-jack"))
            device = args.device
            if jack and not args.no_audio:
                if not shutil.which("pw-jack"):
                    raise RuntimeError("pw-jack is unavailable; select --audio-backend native or install the JACK bridge")
                if device is None:
                    # Query through the same bridge/environment as the child;
                    # do not guess ALSA's 'default' when JACK is requested.
                    code = "import sounddevice as s; a=s.query_hostapis(); d=[(i,v) for i,v in enumerate(s.query_devices()) if 'JACK' in a[v['hostapi']]['name'] and v['max_output_channels']>=2]; print(d[0][1]['name'] if d else '')"
                    device = subprocess.check_output(["pw-jack", python, "-c", code], text=True).strip()
                    if not device:
                        raise RuntimeError("no stereo JACK output device; select an available audio backend/device")
                command = ["pw-jack", *command]
            if device:
                command += ["--device", device]
            if args.no_audio:
                command += ["--no-audio"]
            env = dict(os.environ, PYTHONPATH=str(shaper/"src"))
            child = subprocess.Popen(command, cwd=shaper, env=env)
        with httpx.Client(base_url=url, timeout=.5, trust_env=False) as client:
            deadline = time.monotonic()+15
            while True:
                if child and child.poll() is not None:
                    raise RuntimeError(f"Shaper exited with status {child.returncode}; see its output above")
                try:
                    response = client.get("/api/audio/voices")
                    if response.status_code == 200 or (args.no_audio and response.status_code == 503):
                        break
                    if response.status_code == 404:
                        raise RuntimeError("Shaper lacks the laboratory telemetry API; use the laboratory Shaper branch")
                except httpx.HTTPError:
                    pass
                if time.monotonic() >= deadline:
                    raise RuntimeError("Shaper audio API did not become ready within 15 seconds")
                time.sleep(.1)
        store = SessionStore(args.data_dir, prepare=PreparedRoutes)
        seed_presets(store)
        runtime = LaboratoryRuntime(store, audio=ShaperOutput(url))
        perception = PerceptionSettings(checkpoint=str(Path(args.checkpoint).expanduser().resolve()), device=args.tracking_device)
        app = create_app(args.data_dir, store=store, runtime=runtime, perception=perception, ui_dir=args.ui_dir)
        print(f"\nLaboratorio: http://127.0.0.1:{args.port}\nCtrl+C detiene esta sesión y su Shaper propio.\n", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
    finally:
        if store:
            store.close()
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)


if __name__ == "__main__":
    sys.exit(main())
