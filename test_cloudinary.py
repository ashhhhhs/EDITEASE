import os
import config
from services import cloudinary_service
from utils.logger import setup_logger

logger = setup_logger("test_cloudinary")

def main():
    if not cloudinary_service.is_configured():
        logger.error("Cloudinary is still NOT configured!")
        return
        
    logger.info("Cloudinary is configured. Testing upload and move...")
    
    # Create a dummy text file
    dummy_path = "dummy_test.txt"
    with open(dummy_path, "w") as f:
        f.write("Cloudinary test file.")
        
    # Upload it
    url = cloudinary_service._upload(dummy_path, resource_type="raw", public_id="editease/videos/dummy_test")
    logger.info(f"Upload URL: {url}")
    
    if url:
        # Try moving it
        new_url = cloudinary_service.move_video("editease/videos/dummy_test", "editease/exports/test_folder/dummy_test")
        logger.info(f"Move URL: {new_url}")
        
    if os.path.exists(dummy_path):
        os.remove(dummy_path)

if __name__ == "__main__":
    main()
