# GPU acceleration (WSL2 + TensorFlow-GPU)

The pipeline's dominant cost is **DeepFace emotion + retinaface detection (~90% of compute)**,
and that stage runs on **TensorFlow**. TensorFlow dropped native-Windows GPU support after 2.10,
so the only supported way to give it this machine's **RTX 3060** is to run the Celery worker
inside **WSL2** with a Linux CUDA TensorFlow build and GPU passthrough. The PyTorch scene
classifier stays on CPU by design (see step 3) — it's only ~39 ms/frame, and a GPU torch wheel
conflicts with TF's CUDA libraries.

**Measured speedup on this machine** (retinaface via DeepFace, same 1280px frame, RTX 3060 vs a
forced-CPU run in the same venv): **~1.86 s/frame → ~0.19 s/frame, ≈ 10×** on the emotion stage.

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
pip install deepface tf-keras          # tf-keras is required by DeepFace on TF 2.21 (keras 3)

# requirements.txt does not pin OpenCV, so Linux pulls opencv-python 5.0, whose
# wheel drops cv2.CascadeClassifier (the pipeline needs it). Pin the same 4.x the
# Windows side uses, headless build (no GUI/libGL deps — right for a worker):
pip uninstall -y opencv-python opencv-contrib-python
pip install 'opencv-python-headless==4.13.0.92'

# TensorFlow with GPU (Linux only) — this is the 90% bottleneck, so it gets the GPU:
pip install 'tensorflow[and-cuda]'                      # bundles matching CUDA 12 libs

# torch is the ~39 ms scene classifier — negligible next to TF. Install the CPU
# build: a GPU torch wheel drags in a DIFFERENT CUDA version that shadows TF's
# libraries and breaks TF's GPU detection. CPU torch keeps the venv CUDA-12-clean.
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

> **Why CPU torch?** Mixing a GPU torch (which may pull CUDA 13 libs) with
> `tensorflow[and-cuda]` (CUDA 12) leaves two CUDA versions in one venv; TF then
> can't load its libraries and reports no GPU. TF is the stage that matters, so we
> keep it clean and let torch run on CPU.

### 4. Verify the GPU is visible to TensorFlow
```bash
python -c "import tensorflow as tf; print('TF GPUs:', tf.config.list_physical_devices('GPU'))"
```

This must print a non-empty list with `GPU:0`. **If it prints `[]`**, TF can't find
its CUDA libraries — see *Troubleshooting* below. The launcher script
(`run_worker_wsl.sh`) sets the required `LD_LIBRARY_PATH` automatically, so this only
bites you when running `python` by hand. The first pipeline run also downloads the
DeepFace model weights into `~/.deepface` (needs internet once).

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

---

## Troubleshooting

**`pip install` fails with `externally-managed-environment`.** Your `.venv-linux` was created
without its own pip (the `python3-venv` package wasn't installed yet), so `pip` fell back to the
locked system one. Fix: `sudo apt install -y python3-venv`, then rebuild the venv —
`rm -rf .venv-linux && python3 -m venv .venv-linux` — and re-activate. Confirm with
`which pip` → it must point inside `.venv-linux`, not `/usr/bin/pip`.

**`tf.config.list_physical_devices('GPU')` returns `[]`.** Two causes, both seen on this machine:
- *TF can't find its CUDA libraries.* TF 2.21 does not auto-add the pip `nvidia/*/lib` dirs to the
  loader path on WSL. `run_worker_wsl.sh` exports the correct `LD_LIBRARY_PATH` for you; when
  testing by hand, set it first:
  ```bash
  NV="$PWD/.venv-linux/lib/python3.12/site-packages/nvidia"
  export LD_LIBRARY_PATH="$(ls -d $NV/*/lib | tr '\n' ':')/usr/lib/wsl/lib"
  ```
- *Incomplete cuDNN install.* If an earlier `pip install` was interrupted, `nvidia-cudnn-cu12`
  can be present but missing most of its `.so` files (check
  `ls .venv-linux/lib/python3.12/site-packages/nvidia/cudnn/lib` — you should see ~10 files
  including `libcudnn.so.9`). Fix: `pip install --force-reinstall --no-deps nvidia-cudnn-cu12`.

**PyTorch shows the GPU but TensorFlow doesn't.** Expected here — torch runs on CPU by design (see
step 3). Only TensorFlow needs the GPU.
