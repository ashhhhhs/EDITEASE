# GPU acceleration (WSL2 + TensorFlow-GPU)

The pipeline's dominant cost is **DeepFace emotion + retinaface detection at ~7.9 s/frame
(~90% of compute)**, and that stage runs on **TensorFlow**. TensorFlow dropped native-Windows
GPU support after 2.10, so the only supported way to give it this machine's **RTX 3060** is to
run the Celery worker inside **WSL2** with a Linux CUDA TensorFlow build and GPU passthrough.
The PyTorch scene classifier rides along on the same GPU for free.

Everything else — the Flask API, the React SPA, MongoDB, and Redis — stays on Windows,
unchanged. **Only the Celery worker moves.**

> **One worker at a time.** The GPU (WSL) worker and the Windows CPU worker consume the *same*
> Redis queue. Run one or the other, never both. The GPU path is opt-in; the Windows CPU worker
> remains the always-available fallback.

---

## One-time setup

### 1. Install WSL2 + Ubuntu
From an elevated PowerShell:

```powershell
wsl --install -d Ubuntu-22.04
```

The existing Windows NVIDIA driver already exposes the GPU to WSL — **do not install a Linux
NVIDIA driver.** Verify inside the Ubuntu shell:

```bash
nvidia-smi   # should list the RTX 3060
```

### 2. Enable mirrored networking (recommended)
So `localhost` inside WSL reaches the Windows-hosted Redis and MongoDB and the shared `.env`
works unchanged. Create/edit `%UserProfile%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Then `wsl --shutdown` and reopen the Ubuntu shell. (If you can't use mirrored networking, use
the host-IP overrides commented in `scripts/run_worker_wsl.sh` instead.)

### 3. Create the Linux venv and install GPU wheels
The Windows `.venv\Scripts` is **not** reusable on Linux — make a separate one. From the Ubuntu
shell (the Windows checkout is mounted at `/mnt/d/EDITEASE`):

```bash
cd /mnt/d/EDITEASE
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install deepface

# GPU builds (Linux only):
pip install 'tensorflow[and-cuda]'                      # bundles matching CUDA 12 libs
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

### 4. Verify the GPU is visible to both stacks
```bash
python -c "import tensorflow as tf; print('TF GPUs:', tf.config.list_physical_devices('GPU'))"
python -c "import torch; print('torch CUDA:', torch.cuda.is_available())"
```

Both must report the GPU. The first pipeline run also re-downloads the DeepFace model weights
into `~/.deepface` (needs internet once).

---

## Running the GPU worker

From the Ubuntu shell:

```bash
cd /mnt/d/EDITEASE
./scripts/run_worker_wsl.sh
```

The script activates `.venv-linux`, sets `EE_WSL_PATHS=1` and `TF_FORCE_GPU_ALLOW_GROWTH=true`,
and starts the worker with `--pool=solo`. **Do not raise concurrency** — 6 GB VRAM only
comfortably holds one video's models at a time.

Start the Windows API and frontend as usual; upload a video from the SPA. Watch utilization
climb during the emotion stage:

```bash
watch -n 1 nvidia-smi
```

## Falling back to the CPU worker

Stop the WSL worker (Ctrl-C), then from PowerShell on Windows:

```powershell
.\.venv\Scripts\python.exe -m celery -A api.celery_worker.celery_app worker --pool=solo
```

Same code, same queue, no GPU. This is the demo-safe default.

---

## How the path translation works

Tasks are enqueued on Windows with absolute Windows path strings (`str(config.BASE_DIR)` =
`D:\EDITEASE`, plus a `D:\...` video path — see `services/task_service.py`). Inside WSL those
same files live under `/mnt/d/EDITEASE`. `api/celery_worker.py` contains a small `_localize_path`
shim that rewrites drive-letter paths to their `/mnt` mount at the top of each task.

It is a strict **no-op** unless the host is POSIX **and** `EE_WSL_PATHS=1` is set (only the WSL
launcher sets it), so the native-Windows worker is completely unaffected.

**Residual caveat:** thumbnails and clips are normally served from Cloudinary URLs
(`resolve_thumbnail` / `resolve_video_path` prefer the cloud URL), so the local paths the worker
stores don't matter to the Windows API. But if a Cloudinary upload *fails*, the worker records a
`/mnt/...` local-path fallback that the Windows API can't resolve — that one asset renders broken
until reprocessed. Cloudinary is the normal path, so this is a rare degradation.
