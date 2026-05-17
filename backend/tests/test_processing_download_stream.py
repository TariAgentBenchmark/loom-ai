import io
import zipfile

import pytest

from app.utils.streaming_downloads import iter_streaming_zip


class _FakeOssService:
    bucket = None


class _FakeFileService:
    def __init__(self, upload_path):
        self.upload_path = str(upload_path)
        self.oss_service = _FakeOssService()

    def extract_oss_object_key(self, file_url):
        return None


@pytest.mark.asyncio
async def test_streaming_zip_outputs_valid_archive_and_normalizes_extensions(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "image.bin").write_bytes(b"\x89PNG\r\n\x1a\npng-data")
    (results_dir / "vector.bin").write_bytes(b"%!PS-Adobe-3.0 EPSF-3.0\n")

    file_service = _FakeFileService(tmp_path)
    chunks = [
        chunk
        async for chunk in iter_streaming_zip(
            file_service,
            [
                ("/files/results/image.bin", "image.dat"),
                ("/files/results/vector.bin", "vector.png"),
            ],
        )
    ]

    with zipfile.ZipFile(io.BytesIO(b"".join(chunks))) as archive:
        assert sorted(archive.namelist()) == ["image.png", "vector.eps"]
        assert archive.read("image.png").startswith(b"\x89PNG")
        assert archive.read("vector.eps").startswith(b"%!PS")
