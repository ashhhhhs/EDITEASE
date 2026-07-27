"""_compress_video_for_upload gates encoding correctly and degrades gracefully.

Large videos are transcoded before upload (smaller/faster, fits under Cloudinary
limits); small files skip it, and any encoder failure falls back to the original
so an upload can never be blocked. These tests simulate ffmpeg rather than run it.
"""
import os

import pytest

import config
from services import cloudinary_service as cs


def _make_file(path, size):
    with open(path, "wb") as fh:
        fh.write(b"\0" * size)


def test_disabled_returns_original(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_ENABLED", False)
    src = tmp_path / "big.mp4"
    _make_file(src, 1_000)
    assert cs._compress_video_for_upload(str(src)) == (str(src), False)


def test_small_file_skips_encode(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_ENABLED", True)
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_THRESHOLD_BYTES", 10_000)
    src = tmp_path / "small.mp4"
    _make_file(src, 500)  # under threshold
    # subprocess must never be called for a small file
    monkeypatch.setattr(cs.subprocess, "run", lambda *a, **k: pytest.fail("encoded a small file"))
    assert cs._compress_video_for_upload(str(src)) == (str(src), False)


def test_large_file_compresses(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_ENABLED", True)
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_THRESHOLD_BYTES", 1_000)
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_CQ", 23)
    src = tmp_path / "big.mp4"
    _make_file(src, 50_000)  # over threshold

    def fake_run(cmd, **kwargs):
        _make_file(cmd[-1], 5_000)  # encoder writes a smaller file to the temp path
        return None

    monkeypatch.setattr(cs.subprocess, "run", fake_run)
    out, is_temp = cs._compress_video_for_upload(str(src))
    assert is_temp is True
    assert out != str(src)
    assert os.path.getsize(out) < os.path.getsize(str(src))
    os.remove(out)  # caller is responsible for cleanup


def test_encoder_failure_falls_back_to_original(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_ENABLED", True)
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_THRESHOLD_BYTES", 1_000)
    src = tmp_path / "big.mp4"
    _make_file(src, 50_000)

    def boom(cmd, **kwargs):
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr(cs.subprocess, "run", boom)
    out, is_temp = cs._compress_video_for_upload(str(src))
    assert (out, is_temp) == (str(src), False)
    # no stray temp files left behind
    assert not any(p.name.startswith("ee_compress_") for p in tmp_path.iterdir())


def test_compression_not_smaller_keeps_original(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_ENABLED", True)
    monkeypatch.setattr(config, "CLOUDINARY_COMPRESS_THRESHOLD_BYTES", 1_000)
    src = tmp_path / "big.mp4"
    _make_file(src, 10_000)

    def fake_run(cmd, **kwargs):
        _make_file(cmd[-1], 20_000)  # "compressed" output is actually larger
        return None

    monkeypatch.setattr(cs.subprocess, "run", fake_run)
    out, is_temp = cs._compress_video_for_upload(str(src))
    assert (out, is_temp) == (str(src), False)
