import sys
import os
import shutil
import requests
import pymongo
from pymongo.errors import ConnectionFailure
from urllib.error import URLError

import config


def check_mongo():
    print("Checking MongoDB Connection...")
    try:
        client = pymongo.MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print("✅ MongoDB connection successful.")
        return True
    except ConnectionFailure:
        print(f"❌ Failed to connect to MongoDB at {config.MONGO_URI}")
        return False
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return False

def check_api():
    print(f"\nChecking Flask API at {config.API_HOST}:{config.API_PORT}...")
    url = f"http://{config.API_HOST}:{config.API_PORT}/health"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            print("✅ API is responding correctly.")
            return True
        else:
            print(f"❌ API returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API is unreachable. Is the Flask server running?")
        return False
    except Exception as e:
        print(f"❌ API error: {e}")
        return False

def check_redis():
    print("\nChecking Redis (Celery Broker)...")
    try:
        import redis
        # Parse the broker URL
        client = redis.from_url(config.CELERY_BROKER_URL, socket_timeout=2)
        client.ping()
        print(f"✅ Redis connection successful at {config.CELERY_BROKER_URL}")
        return True
    except redis.exceptions.ConnectionError:
        print(f"❌ Redis is unreachable at {config.CELERY_BROKER_URL}. Is Redis server running?")
        return False
    except ImportError:
        print("❌ 'redis' python package not installed.")
        return False
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False

def check_ffmpeg():
    print("\nChecking FFmpeg installation...")
    # FFMPEG_PATH may be an absolute path OR a bare command name resolved via
    # PATH — SETUP.md documents `FFMPEG_PATH=ffmpeg`, for which os.path.exists
    # is always False. Fall back to a PATH lookup before declaring it missing.
    ffmpeg_cmd = config.FFMPEG_PATH
    if not os.path.exists(ffmpeg_cmd):
        resolved = shutil.which(ffmpeg_cmd)
        if not resolved:
            print(f"❌ FFmpeg not found at {ffmpeg_cmd} and not on PATH")
            return False
        ffmpeg_cmd = resolved

    import subprocess
    try:
        result = subprocess.run([ffmpeg_cmd, "-version"],
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              text=True)
        if result.returncode == 0:
            # Print just the first line of the version info
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg found: {version_line}")
            return True
        else:
            print("❌ FFmpeg execution failed.")
            return False
    except Exception as e:
        print(f"❌ Error running FFmpeg: {e}")
        return False


if __name__ == "__main__":
    print(f"{'='*40}")
    print("EditEase Health Check")
    print(f"{'='*40}\n")
    
    db_ok = check_mongo()
    api_ok = check_api()
    redis_ok = check_redis()
    ffmpeg_ok = check_ffmpeg()
    
    print(f"\n{'='*40}")
    if db_ok and api_ok and redis_ok and ffmpeg_ok:
        print("🎉 All systems functioning normally!")
        sys.exit(0)
    else:
        print("⚠️ Some systems are failing. Check the logs above.")
        sys.exit(1)
