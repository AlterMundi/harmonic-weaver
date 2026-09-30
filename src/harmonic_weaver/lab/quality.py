"""Coverage describes observation availability, never physical accuracy."""
from collections import Counter


def coverage(frames, *, start_s=0., end_s=None, person_id=None):
    if not frames:
        return {"duration_s": 0., "persons": {}, "warning": "Sin observaciones"}
    end_s = end_s if end_s is not None else frames[-1].source_time_s + (frames[-1].duration_s or 1/30)
    ids = [person_id] if person_id else sorted({p.person_id for f in frames for p in f.persons})
    result = {}
    for pid in ids:
        joints = {i: {"observed_s": 0., "held_s": 0., "missing_s": 0., "max_gap_s": 0.} for i in range(17)}
        leading = max(0., min(end_s, frames[0].source_time_s)-start_s)
        gaps = {i: leading for i in joints}
        count = 0
        for index, frame in enumerate(frames):
            following = frames[index+1].source_time_s if index+1 < len(frames) else end_s
            left, right = max(start_s, frame.source_time_s), min(end_s, following)
            if right <= left:
                continue
            count += 1
            # Never fill a timestamp gap by stretching one observed frame.
            observed_end = min(right, frame.source_time_s + min(frame.duration_s or following-frame.source_time_s, .25))
            observed_dt, absent_dt = max(0., observed_end-left), right-max(left, observed_end)
            person = next((p for p in frame.persons if p.person_id == pid), None)
            points = {j.index: j for j in person.joints} if person else {}
            for i, totals in joints.items():
                joint = points.get(i)
                state = joint.state if joint and joint.position is not None else "missing"
                totals[state+"_s"] += observed_dt
                totals["missing_s"] += absent_dt
                if state == "observed" and observed_dt > 0:
                    gaps[i] = 0.
                else:
                    gaps[i] += observed_dt
                gaps[i] += absent_dt
                totals["max_gap_s"] = max(totals["max_gap_s"], gaps[i])
        # Account for an empty leading interval.
        leading = max(0., min(end_s, frames[0].source_time_s)-start_s)
        for totals in joints.values():
            totals["missing_s"] += leading
            totals["max_gap_s"] = max(totals["max_gap_s"], leading)
            totals["observed_fraction"] = totals["observed_s"]/max(end_s-start_s, 1e-12)
        result[pid] = {"frames": count, "joints": joints}
    return {"start_s": start_s, "end_s": end_s, "duration_s": max(0., end_s-start_s),
            "persons": result, "warning": "Cobertura de observaciones; no mide precisión ni descarta oclusiones."}


def current_quality(frame, person_id):
    person = next((p for p in frame.persons if p.person_id == person_id), None) if frame else None
    states = Counter(j.state for j in person.joints) if person else Counter()
    return {"observed": states["observed"], "held": states["held"],
            "missing": 17-states["observed"]-states["held"],
            "warning": "Observado no equivale a pose correcta."}
