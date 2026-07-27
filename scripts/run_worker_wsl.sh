#!/usr/bin/env bash
#
# Launch the EditEase Celery worker inside WSL2 with GPU acceleration.
#
# This is the GPU path from SETUP-GPU.md. It runs the SAME code as the Windows
# worker, but under a Linux venv where TensorFlow (DeepFace/retinaface) and
# PyTorch can use the RTX 3060 via WSL2 GPU passthrough.
#
# Only ONE worker may consume the Redis queue at a time. Start this OR the
# Windows worker, never both. To fall back to CPU, stop this and start the
# Windows worker instead (see SETUP-GPU.md).
#
# Usage (from a WSL2 Ubuntu shell):
#   ./scripts/run_worker_wsl.sh
#
set -euo pipefail

# Project root as seen from WSL. The Windows checkout at D:\EDITEASE is mounted
# here, so config.BASE_DIR, .env and pipeline/models/ all resolve to it.
PROJECT_DIR="${EE_PROJECT_DIR:-/mnt/d/EDITEASE}"
# Separate Linux venv — the Windows .venv\Scripts is not reusable on Linux.
VENV_DIR="${EE_VENV_DIR:-$PROJECT_DIR/.venv-linux}"

cd "$PROJECT_DIR"

if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
  echo "Linux venv not found at $VENV_DIR — see SETUP-GPU.md for the one-time setup." >&2
  exit 1
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

# Turn on the WSL path-translation shim in api/celery_worker.py so the "D:\..."
# task args enqueued on Windows are opened as "/mnt/d/...".
export EE_WSL_PATHS=1
# 6 GB VRAM is tight; let TensorFlow grow its allocation instead of grabbing all.
export TF_FORCE_GPU_ALLOW_GROWTH=true

# TensorFlow 2.21 does NOT auto-discover the pip-installed CUDA libraries on WSL,
# so without this it silently falls back to CPU (tf.config.list_physical_devices
# ("GPU") == []). Point the dynamic loader at the nvidia/*/lib dirs in the venv,
# plus the WSL driver stub at /usr/lib/wsl/lib.
NV_LIBS="$(python -c 'import os,glob,nvidia; b=os.path.dirname(nvidia.__file__); print(":".join(sorted(glob.glob(b+"/*/lib"))))' 2>/dev/null || true)"
if [[ -n "$NV_LIBS" ]]; then
  export LD_LIBRARY_PATH="$NV_LIBS:/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# --- Networking (uncomment only if WSL2 mirrored networking is NOT enabled) ---
# Without mirrored networking, localhost inside WSL does not reach the Windows
# Redis/MongoDB. Point these at the Windows host IP instead:
#   WIN_HOST=$(ip route show default | awk '{print $3}')
#   export MONGO_URI="mongodb://$WIN_HOST:27017"
#   export CELERY_BROKER_URL="redis://$WIN_HOST:6379/0"
#   export CELERY_RESULT_BACKEND="redis://$WIN_HOST:6379/1"

# --pool=solo: one video at a time. Do NOT raise concurrency on a 6 GB GPU.
exec python -m celery -A api.celery_worker.celery_app worker --pool=solo "$@"
