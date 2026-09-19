from pathlib import Path
import hashlib
import sys
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from phase10_download_nse_sample import download


def test_download_inventory_with_mocked_response(tmp_path, monkeypatch):
    payload = tmp_path / "source.zip"
    with ZipFile(payload, "w") as zf:
        zf.writestr("sample.csv.gz", b"test")

    class FakeResponse:
        headers = {"content-type": "application/zip"}

        def raise_for_status(self):
            return None

        @property
        def content(self):
            return payload.read_bytes()

    monkeypatch.setattr(
        "phase10_download_nse_sample.requests.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    out = tmp_path / "copy.zip"
    manifest = download("https://example.invalid/sample.zip", out)
    assert manifest["bytes"] == out.stat().st_size
    assert manifest["sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()
    assert manifest["archive_entries"] == ["sample.csv.gz"]
