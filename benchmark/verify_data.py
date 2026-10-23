"""Verify downloaded datasets against their saved, exact local manifests."""
import csv
import hashlib
import json
import sys
from pathlib import Path


def verify(path):
    p = Path(path)
    manifest_path = p.with_suffix('.manifest.json')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual_hash != manifest['csv_sha256']:
        raise ValueError(f'SHA256 mismatch: {p}')
    if not (isinstance(manifest['revision_sha'], str) and len(manifest['revision_sha']) == 40):
        raise ValueError(f'Invalid pinned revision: {p}')
    with p.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != manifest['rows'] or len(rows) != len(manifest['sample_indices']):
        raise ValueError(f'Row count mismatch: {p}')
    if len({row['task_id'] for row in rows}) != len(rows):
        raise ValueError(f'Duplicate task ID: {p}')
    if any(not row['prompt'] or not row['expected'] for row in rows):
        raise ValueError(f'Incomplete task: {p}')
    return {'file': str(p), 'rows': len(rows), 'sha256': actual_hash, 'source': manifest['source_url'], 'revision': manifest['revision_sha']}


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python -m benchmark.verify_data FILE.csv [FILE.csv ...]')
    for filename in sys.argv[1:]:
        print(json.dumps(verify(filename), ensure_ascii=False))


if __name__ == '__main__':
    main()
