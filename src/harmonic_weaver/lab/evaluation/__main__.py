import argparse
from pathlib import Path
from .runner import Request, run

def main():
    parser = argparse.ArgumentParser(description="Replay causal de presets × fuentes; sin audio")
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    request = Request.model_validate_json(args.request.read_text())
    result = run(request, args.output, progress=lambda n, total: print(f"{n}/{total}", flush=True))
    print(f"{result['status']}: {args.output / 'manifest.json'}")

if __name__ == "__main__":
    main()
