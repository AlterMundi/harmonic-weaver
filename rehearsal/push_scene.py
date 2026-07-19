"""Push a scene to a running Weaver Stage over the WebSocket protocol.

Standalone helper for live sessions: the rehearsal runner does this inline,
but a live stack launched by scripts/start-live-stack.sh needs a small CLI
to upsert a scene file and optionally make it the active scene.

Usage:
    PYTHONPATH=src:. python rehearsal/push_scene.py \
        --scene rehearsal/scenes/event_demo.scene.json --switch

    # Upsert without activating:
    python rehearsal/push_scene.py --scene rehearsal/scenes/sparse.scene.json

    # Only switch to an already-installed scene:
    python rehearsal/push_scene.py --switch-only sparse
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rehearsal.runner import StageClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default="ws://127.0.0.1:8765/ws",
                        help="Stage WebSocket endpoint")
    parser.add_argument("--scene", type=Path, default=None,
                        help="scene JSON file to upsert")
    parser.add_argument("--switch", action="store_true",
                        help="activate the upserted scene after upserting")
    parser.add_argument("--switch-only", default=None, metavar="SCENE_ID",
                        help="only switch to an already-installed scene")
    parser.add_argument("--scene-version", type=int, default=1,
                        help="expected scene version for the switch command")
    args = parser.parse_args(argv)

    if args.switch_only and args.scene:
        parser.error("--switch-only and --scene are mutually exclusive")
    if not args.switch_only and not args.scene:
        parser.error("provide --scene or --switch-only")

    stage = StageClient(args.uri)
    try:
        if args.switch_only:
            stage.switch_scene(args.switch_only, scene_version=args.scene_version)
            print(f"[push_scene] active scene: {args.switch_only}")
            return 0

        scene = json.loads(args.scene.read_text(encoding="utf-8"))
        scene_id = scene.get("scene_id") or scene.get("id")
        if not scene_id:
            print(f"[push_scene] ERROR: {args.scene} has no scene_id", file=sys.stderr)
            return 2
        stage.upsert_scene(scene)
        print(f"[push_scene] upserted scene: {scene_id} (from {args.scene})")
        if args.switch:
            stage.switch_scene(scene_id, scene_version=args.scene_version)
            print(f"[push_scene] active scene: {scene_id}")
        return 0
    finally:
        stage.close()


if __name__ == "__main__":
    raise SystemExit(main())
