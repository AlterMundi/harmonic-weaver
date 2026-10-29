import {useEffect, useRef, useState} from "react";

/** Refresh the camera independently of whether its pose is recent enough to use. */
export function CameraPreview({streamId}: {streamId?: string}) {
  const [request, setRequest] = useState(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => {
    if (timer.current !== null) clearTimeout(timer.current);
  }, []);

  const next = (delay: number) => {
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = setTimeout(() => setRequest(value => value + 1), delay);
  };

  return <img alt="Cámara en vivo"
    src={`/api/camera/preview?stream=${encodeURIComponent(streamId || "camera")}&preview=${request}`}
    onLoad={() => next(100)} onError={() => next(500)}/>;
}
