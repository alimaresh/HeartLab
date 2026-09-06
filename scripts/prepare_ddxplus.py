"""Create a compact four-condition training subset from the official DDXPlus archive."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import random
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data' / 'ddxplus'
ARCHIVE = OUTPUT / 'release_validate_patients.zip'
DATA = OUTPUT / 'cardiac_subset.csv'
CONDITIONS = OUTPUT / 'release_conditions.json'
EVIDENCES = OUTPUT / 'release_evidences.json'
FILES = {
    ARCHIVE: ('https://ndownloader.figshare.com/files/40278022', 'e4db88e9082f18410de6fd0cb7e74d18'),
    EVIDENCES: ('https://ndownloader.figshare.com/files/40278013', '0660962abe0bbf99e1fb77188c253597'),
    CONDITIONS: ('https://ndownloader.figshare.com/files/62561569', 'a992eadcff3099dd72e1820fbd2115aa'),
}
PATHOLOGIES = {
    'Stable angina': 'stable_angina',
    'Atrial fibrillation': 'atrial_fibrillation',
    'Possible NSTEMI / STEMI': 'heart_attack',
    'Acute pulmonary edema': 'pulmonary_edema',
}
EVIDENCE_FEATURES = {
    'chest_pain': 'E_53',
    'shortness_of_breath': 'E_66',
    'palpitations': 'E_155',
    'exercise_worse': 'E_218',
    'hypertension': 'E_104',
    'dizziness': 'E_76',
    'sweating': 'E_50',
    'fatigue': 'E_175',
    'swelling': 'E_151',
    'orthopnea': 'E_217',
}


def download(path, url, expected_md5, size=None):
    if path.exists() and hashlib.md5(path.read_bytes()).hexdigest() == expected_md5:
        return
    request = urllib.request.Request(url, headers={'User-Agent': 'HeartLab academic dataset downloader'})
    with urllib.request.urlopen(request, timeout=300) as response, path.open('wb') as destination:
        while block := response.read(1024 * 1024):
            destination.write(block)
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest != expected_md5:
        raise RuntimeError(f'Checksum mismatch for {path.name}: {digest}')


def prepare(archive=ARCHIVE, destination=DATA, limit_per_class=5000):
    reservoirs = {label: [] for label in PATHOLOGIES.values()}
    seen = {label: 0 for label in PATHOLOGIES.values()}
    rng = random.Random(42)
    with zipfile.ZipFile(archive) as source:
        # Figshare currently stores this CSV as ``release_validate_patients``
        # without a file extension inside the ZIP archive.
        names = [name for name in source.namelist() if not name.endswith('/')]
        if len(names) != 1:
            raise RuntimeError(f'Expected one CSV in DDXPlus archive, found {names}')
        with source.open(names[0]) as binary:
            rows = csv.DictReader((line.decode('utf-8') for line in binary))
            for source_row, row in enumerate(rows, start=2):
                if row['PATHOLOGY'] not in PATHOLOGIES:
                    continue
                disease = PATHOLOGIES[row['PATHOLOGY']]
                evidence = set(ast.literal_eval(row['EVIDENCES']))
                record = {
                    'source_row': source_row,
                    'age': int(row['AGE']),
                    'sex': 1 if row['SEX'] == 'M' else 0,
                    **{feature: int(code in evidence) for feature, code in EVIDENCE_FEATURES.items()},
                    'disease': disease,
                }
                seen[disease] += 1
                bucket = reservoirs[disease]
                if len(bucket) < limit_per_class:
                    bucket.append(record)
                else:
                    index = rng.randrange(seen[disease])
                    if index < limit_per_class:
                        bucket[index] = record
    records = [record for label in PATHOLOGIES.values() for record in reservoirs[label]]
    if any(len(reservoirs[label]) < 100 for label in reservoirs):
        raise RuntimeError(f'Insufficient selected records: {seen}')
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)
    return {'source_counts': seen, 'saved_counts': {key: len(value) for key, value in reservoirs.items()}}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path, (url, digest) in FILES.items():
        download(path, url, digest, 18706053 if path == ARCHIVE else None)
    result = prepare()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
