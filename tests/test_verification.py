import csv
import hashlib
import json
import pytest
from benchmark.verify_data import verify

def test_integrity_and_corruption(tmp_path):
    p = tmp_path / 'dataset.csv'
    with p.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['task_id','prompt','expected'])
        w.writeheader()
        w.writerow({'task_id':'test1','prompt':'schema test only','expected':'A'})
    meta = {'csv_sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'revision_sha':'a'*40,
            'rows':1, 'sample_indices':[0], 'source_url':'https://example.invalid/test'}
    p.with_suffix('.manifest.json').write_text(json.dumps(meta))
    assert verify(p)['rows'] == 1
    p.write_text('tampered')
    with pytest.raises(ValueError, match='SHA256 mismatch'):
        verify(p)
