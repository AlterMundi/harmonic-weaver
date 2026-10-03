"""Follow one explicit Shaper recovery receipt; GET never restarts a writer."""
import time

import httpx


class UnconfirmedRecovery(ValueError):
    pass


def recover(client, capture_id, job_id, *, timeout_s=120, interval_s=.25):
    path = f'/api/audio/capture/recovery-jobs/{job_id}'
    deadline = time.monotonic()+timeout_s
    while time.monotonic() < deadline:
        try:
            response = client.get(path, timeout=8)
            if response.status_code == 404:
                # Only a confirmed missing receipt permits an idempotent POST.
                response = client.post('/api/audio/capture/recovery-jobs',
                                       json={'id': capture_id, 'job_id': job_id}, timeout=8)
            if response.status_code >= 500:
                time.sleep(interval_s)
                continue
            response.raise_for_status()
            report = response.json()
        except httpx.TransportError:
            time.sleep(interval_s)
            continue
        if report.get('job_id') != job_id or report.get('capture_id') != capture_id:
            raise ValueError('Shaper recovery receipt identity differs')
        if report['status'] == 'recovered':
            result = report.get('result', {})
            if result.get('status') != 'recovered' or result.get('capture_id') != capture_id:
                raise ValueError('Shaper recovered result identity differs')
            return result
        if report['status'] not in ('queued', 'running'):
            raise ValueError(f"Shaper recovery {report['status']}: {report.get('error', '')}")
        time.sleep(interval_s)
    raise UnconfirmedRecovery('Shaper recovery remains unconfirmed; receipt retained for explicit retry')
