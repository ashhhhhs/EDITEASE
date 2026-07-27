"""Thin wrapper around the Cloudinary SDK for EDITEASE uploads."""

import cloudinary
import cloudinary.uploader
import cloudinary.utils

import config
from utils.logger import setup_logger

logger = setup_logger("cloudinary_service")

cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)

# The SDK builds its HTTP pool with urllib3's default maxsize=1, so the
# UPLOAD_WORKERS threads that upload thumbnails concurrently (see run_pipeline)
# serialize on a single connection and re-handshake TLS each time — the
# "Connection pool is full, discarding connection. Connection pool size: 1"
# warning. Rebuild the pool with a maxsize matching the worker count so those
# uploads run in parallel and reuse connections. Uses the SDK's own connector
# factory so TCP keep-alive behaviour is preserved.
try:
    _pool_opts = {**cloudinary.CERT_KWARGS, "maxsize": max(config.UPLOAD_WORKERS, 8)}
    cloudinary.uploader._http = cloudinary.utils.get_http_connector(
        cloudinary.config(), _pool_opts,
    )
except Exception as exc:  # a pool tweak must never break uploads
    logger.warning("Could not enlarge Cloudinary connection pool: %s", exc)


def is_configured() -> bool:
    return all([
        config.CLOUDINARY_CLOUD_NAME,
        config.CLOUDINARY_API_KEY,
        config.CLOUDINARY_API_SECRET,
    ])


def _upload(local_path: str, resource_type: str, public_id: str | None = None) -> str | None:
    if not is_configured():
        logger.warning(
            "Cloudinary credentials are not configured; skipping %s upload for %s",
            resource_type,
            local_path,
        )
        return None

    try:
        opts = {"resource_type": resource_type}
        if public_id:
            opts["public_id"] = public_id
            
        if resource_type == "video":
            # upload_large chunks the file, preventing SSLEOFError hangs on large files
            result = cloudinary.uploader.upload_large(local_path, **opts)
        else:
            result = cloudinary.uploader.upload(local_path, **opts)
            
        url = result.get("secure_url") # type: ignore
        logger.info("Uploaded %s to Cloudinary: %s", resource_type, url)
        return url
    except Exception as exc:
        logger.error("Cloudinary %s upload failed: %s", resource_type, exc)
        return None


def upload_video(local_path: str, public_id: str | None = None) -> str | None:
    """Upload a video file to Cloudinary and return its secure URL."""
    return _upload(local_path, resource_type="video", public_id=public_id)


def upload_image(local_path: str, public_id: str | None = None) -> str | None:
    """Upload an image file to Cloudinary and return its secure URL."""
    return _upload(local_path, resource_type="image", public_id=public_id)


def delete_asset(public_id: str, resource_type: str = "image") -> bool:
    """Delete a Cloudinary asset by public_id."""
    if not is_configured():
        logger.warning(
            "Cloudinary credentials are not configured; skipping delete for %s",
            public_id,
        )
        return False

    try:
        cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        logger.info("Deleted Cloudinary asset: %s", public_id)
        return True
    except Exception as exc:
        logger.error("Cloudinary delete failed: %s", exc)
        return False

def move_video(old_public_id: str, new_public_id: str) -> str | None:
    """Rename/move a Cloudinary video asset from one folder to another."""
    if not is_configured():
        logger.warning("Cloudinary credentials not configured; skipping move.")
        return None

    try:
        res = cloudinary.uploader.rename(old_public_id, new_public_id, overwrite=True, resource_type="video")
        logger.info("Moved Cloudinary video: %s -> %s", old_public_id, new_public_id)
        return res.get("secure_url")
    except Exception as exc:
        logger.error("Cloudinary move failed: %s", exc)
        return None


def upload_video_returning_id(local_path: str, public_id: str) -> tuple[str, str] | tuple[None, None]:
    """Upload a video and return (secure_url, public_id). Used by hash-safe organize flow."""
    if not is_configured():
        logger.warning("Cloudinary credentials not configured; skipping upload.")
        return None, None
    try:
        # upload_large chunks the file, preventing network hangs on large files
        result = cloudinary.uploader.upload_large(
            local_path,
            resource_type="video",
            public_id=public_id,
        )
        url = result.get("secure_url") # type: ignore
        pid = result.get("public_id", public_id) # type: ignore
        logger.info("Uploaded video to Cloudinary: %s -> %s", pid, url)
        return url, pid
    except Exception as exc:
        logger.error("Cloudinary upload_video_returning_id failed: %s", exc)
        return None, None


def move_video_returning_id(old_public_id: str, new_public_id: str) -> tuple[str, str] | tuple[None, None]:
    """Rename a Cloudinary video and return (secure_url, new_public_id). Used by hash-safe organize flow."""
    if not is_configured():
        logger.warning("Cloudinary credentials not configured; skipping move.")
        return None, None
    try:
        res = cloudinary.uploader.rename(old_public_id, new_public_id, overwrite=True, resource_type="video")
        url = res.get("secure_url")
        pid = res.get("public_id", new_public_id)
        logger.info("Moved Cloudinary video: %s -> %s", old_public_id, pid)
        return url, pid
    except Exception as exc:
        logger.error("Cloudinary move_video_returning_id failed: %s", exc)
        return None, None

