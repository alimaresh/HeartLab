"""Re-fetch the exact public files used by the educational screening experiment."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile

URL = 'https://archive.ics.uci.edu/static/public/45/heart+disease.zip'
EXPECTED = 'b8e4bbd06b9bf9ec831c992ba397639f22815e525c43b489e1a6e75b3be29a75'


def download():
    archive = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL, timeout=60).read()))
    raw = archive.read('hungarian.data')
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('Source changed; review it before replacing the verified training data')
    target = Path(__file__).resolve().parents[1] / 'data' / 'uci'
    target.mkdir(parents=True, exist_ok=True)
    (target / 'hungarian.data').write_bytes(raw)
    (target / 'heart-disease.names').write_bytes(archive.read('heart-disease.names'))
    print('Verified UCI Hungarian dataset downloaded. See data/uci/README.md for attribution.')


if __name__ == '__main__':
    download()
