"""Explicit R04 synthetic HTTP server: no runtime/audio/tracking devices."""
import argparse
from pathlib import Path
import uvicorn
from harmonic_weaver.lab.app import create_app


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--ui',type=Path,required=True);parser.add_argument('--port',type=int,default=8879)
    args=parser.parse_args();args.root.mkdir(parents=True,exist_ok=False)
    uvicorn.run(create_app(args.root,ui_dir=args.ui),host='127.0.0.1',port=args.port)


if __name__=='__main__':main()
