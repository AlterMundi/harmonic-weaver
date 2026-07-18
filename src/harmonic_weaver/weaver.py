"""Run the headless Weaver server with ``python -m harmonic_weaver.weaver``."""

from __future__ import annotations

import argparse

from .engine import ReportWriter, WeaverEngine
from .server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Harmonic Weaver headless routing engine")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--report-root", default="reports")
    parser.add_argument("--run-id")
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("uvicorn is required; install harmonic-weaver runtime dependencies") from exc

    report = ReportWriter(args.report_root, run_id=args.run_id, run_config={"bind_host": args.host, "bind_port": args.port})
    engine = WeaverEngine(report_writer=report)
    uvicorn.run(create_app(engine), host=args.host, port=args.port, log_level=args.log_level)
    engine.close()


if __name__ == "__main__":
    main()
