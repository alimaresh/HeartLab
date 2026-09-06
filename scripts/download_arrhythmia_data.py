"""Download and verify the official UCI Arrhythmia source files."""
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

URL = 'https://archive.ics.uci.edu/static/public/5/arrhythmia.zip'
EXPECTED_DATA_SHA256 = 'a7f0f4ca289a4c58b5ed85a9adb793189acd38425828ce3dfbb70adb45f30169'
DESTINATION = Path(__file__).resolve().parents[1] / 'data' / 'arrhythmia'


def main():
    with urllib.request.urlopen(URL, timeout=30) as response:
        archive = response.read()
    with zipfile.ZipFile(io.BytesIO(archive)) as source:
        data = source.read('arrhythmia.data')
        names = source.read('arrhythmia.names')
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_DATA_SHA256:
        raise RuntimeError(f'Unexpected data checksum: {digest}')
    DESTINATION.mkdir(parents=True, exist_ok=True)
    (DESTINATION / 'arrhythmia.data').write_bytes(data)
    (DESTINATION / 'arrhythmia.names').write_bytes(names)
    print(f'Verified {len(data):,} bytes in {DESTINATION}')


if __name__ == '__main__':
    main()

