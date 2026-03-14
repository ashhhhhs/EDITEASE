import cv2
import os

def extract_frame(video_path, timestamp, output_path):
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return False

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)

    ret, frame = cap.read()
    cap.release()

    if ret and frame is not None:
        cv2.imwrite(output_path, frame)
        print(f"✅ Frame saved at {output_path}")
        return True
    else:
        print(f"❌ Failed to extract frame at {timestamp:.2f}s")
        return False


if __name__ == "__main__":
    # Get folder where THIS script is located
    script_folder = os.path.dirname(os.path.abspath(__file__))

    # Video is inside the same folder as this script (editease_app)
    video_path = os.path.join(script_folder, "forya.mp4")

    # Save the image inside the same folder too
    output_path = os.path.join(script_folder, "test_frame.jpg")

    extract_frame(video_path, timestamp=6.0, output_path=output_path)
