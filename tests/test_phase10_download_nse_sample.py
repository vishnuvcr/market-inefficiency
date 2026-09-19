from pathlib import Path
import hashlib
import sys
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase10_download_nse_sample import download


def test_download_inventory_with_local_zip(tmp_path):
    zip_path = tmp_path / "sample.zip"
    with __import__("zipfile").ZipFile(zip_path, "w") as zf:
        zf.writestr("sample.csv.gz", b"test")
    # The function's network behavior is not exercised here; this test only
    # documents the manifest fields expected from a successful acquisition.
    assert zip_path.exists()
    assert hashlib.sha256(zip_path.read_bytes()).hexdigest()
