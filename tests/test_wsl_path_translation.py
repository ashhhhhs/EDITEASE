"""_localize_path maps Windows paths to WSL /mnt mounts, and only when opted in.

The GPU worker runs inside WSL2 but receives Windows path strings enqueued on
the host (services/task_service.py sends `str(config.BASE_DIR)` and a "D:\\..."
video path). The shim rewrites those at the task boundary. It must be a strict
no-op on the native-Windows worker so the CPU fallback stays untouched.
"""
import pytest

from api import celery_worker


@pytest.fixture
def wsl_enabled(monkeypatch):
    """Pretend we are a POSIX host that opted into path translation."""
    monkeypatch.setattr(celery_worker.os, "name", "posix")
    monkeypatch.setenv("EE_WSL_PATHS", "1")


def test_translates_backslash_drive_path(wsl_enabled):
    assert (
        celery_worker._localize_path(r"D:\EDITEASE\data\clip.mp4")
        == "/mnt/d/EDITEASE/data/clip.mp4"
    )


def test_translates_base_dir(wsl_enabled):
    assert celery_worker._localize_path(r"D:\EDITEASE") == "/mnt/d/EDITEASE"


def test_translates_forward_slash_drive_path(wsl_enabled):
    assert (
        celery_worker._localize_path("C:/Users/dev/video.mov")
        == "/mnt/c/Users/dev/video.mov"
    )


def test_drive_letter_is_lowercased(wsl_enabled):
    assert celery_worker._localize_path(r"E:\x").startswith("/mnt/e/")


@pytest.mark.parametrize("value", [None, ""])
def test_none_and_empty_pass_through(wsl_enabled, value):
    assert celery_worker._localize_path(value) == value


def test_already_posix_path_unchanged(wsl_enabled):
    assert celery_worker._localize_path("/mnt/d/EDITEASE") == "/mnt/d/EDITEASE"


def test_noop_when_flag_absent(monkeypatch):
    """POSIX host but no opt-in flag → paths are left exactly as received."""
    monkeypatch.setattr(celery_worker.os, "name", "posix")
    monkeypatch.delenv("EE_WSL_PATHS", raising=False)
    assert celery_worker._localize_path(r"D:\EDITEASE\x.mp4") == r"D:\EDITEASE\x.mp4"


def test_noop_on_windows_even_with_flag(monkeypatch):
    """Native-Windows worker never translates, even if the flag leaks in."""
    monkeypatch.setattr(celery_worker.os, "name", "nt")
    monkeypatch.setenv("EE_WSL_PATHS", "1")
    assert celery_worker._localize_path(r"D:\EDITEASE\x.mp4") == r"D:\EDITEASE\x.mp4"
