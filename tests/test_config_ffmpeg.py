"""FFMPEG_PATH must not default to a machine-specific absolute path."""
import importlib
import os

import config


def test_ffmpeg_path_defaults_to_bare_command(monkeypatch):
    """With no env override, the default must be resolvable via PATH.

    A hardcoded absolute path to one developer's build directory cannot be a
    correct default; SETUP.md documents `FFMPEG_PATH=ffmpeg`.
    """
    monkeypatch.delenv("FFMPEG_PATH", raising=False)
    reloaded = importlib.reload(config)
    try:
        assert reloaded.FFMPEG_PATH == "ffmpeg"
        assert not os.path.isabs(reloaded.FFMPEG_PATH)
    finally:
        importlib.reload(config)


def test_ffmpeg_path_still_honours_env_override(monkeypatch):
    """An explicit absolute path must still win."""
    monkeypatch.setenv("FFMPEG_PATH", r"C:\custom\ffmpeg.exe")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.FFMPEG_PATH == r"C:\custom\ffmpeg.exe"
    finally:
        monkeypatch.delenv("FFMPEG_PATH", raising=False)
        importlib.reload(config)
