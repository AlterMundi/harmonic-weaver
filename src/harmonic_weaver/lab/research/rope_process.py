"""Bounded, cancellable stdout capture for local FFmpeg tools (POSIX)."""
import os
import selectors
import subprocess
import time


class DecodeCancelled(ValueError):
    pass


def capture(command,*,max_bytes,timeout=60,cancel=None):
    if max_bytes<1 or timeout<=0:raise ValueError('Positive decode budgets required')
    if cancel is not None and cancel.is_set():raise DecodeCancelled('Video decoding cancelled')
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
    output=bytearray();deadline=time.monotonic()+timeout
    selector=selectors.DefaultSelector()
    try:
        os.set_blocking(process.stdout.fileno(),False)
        selector.register(process.stdout,selectors.EVENT_READ)
        eof=False
        while not eof or process.poll() is None:
            if cancel is not None and cancel.is_set():raise DecodeCancelled('Video decoding cancelled')
            remaining=deadline-time.monotonic()
            if remaining<=0:raise ValueError('Video decoding timed out')
            if eof:
                try:process.wait(timeout=min(.05,remaining))
                except subprocess.TimeoutExpired:pass
                continue
            for key,_ in selector.select(min(.05,remaining)):
                chunk=os.read(key.fileobj.fileno(),min(65536,max_bytes-len(output)+1))
                if not chunk:eof=True;selector.unregister(key.fileobj);break
                output.extend(chunk)
                if len(output)>max_bytes:raise ValueError('Video decoding output exceeds budget')
        if process.returncode:raise ValueError('Video decoding failed')
        if cancel is not None and cancel.is_set():raise DecodeCancelled('Video decoding cancelled')
        return bytes(output)
    finally:
        selector.close()
        if process.poll() is None:process.kill()
        process.wait()
        process.stdout.close()
